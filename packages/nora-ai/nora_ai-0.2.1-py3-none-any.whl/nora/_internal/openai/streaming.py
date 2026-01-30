"""
OpenAI 스트리밍 응답 처리
"""

from ..._internal.utils import format_messages
from .utils import extract_detailed_usage


class StreamWrapper:
    """Generator를 context manager로 감싸는 wrapper 클래스"""
    
    def __init__(self, generator, original_response=None):
        self._generator = generator
        self._original_response = original_response
    
    def __iter__(self):
        return self._generator
    
    def __aiter__(self):
        return self._generator

    def __getattr__(self, name):
        # Litellm/OpenAI 내부가 stream 객체의 parse 등 원본 메서드를 기대할 때 위임
        if self._original_response and hasattr(self._original_response, name):
            return getattr(self._original_response, name)
        raise AttributeError(name)
    
    def __enter__(self):
        # 원본 response가 context manager를 지원하면 사용
        if self._original_response and hasattr(self._original_response, '__enter__'):
            self._original_response.__enter__()
        return self
    
    def __exit__(self, *args):
        # 원본 response가 context manager를 지원하면 사용
        if self._original_response and hasattr(self._original_response, '__exit__'):
            return self._original_response.__exit__(*args)
        return False
    
    async def __aenter__(self):
        # 원본 response가 async context manager를 지원하면 사용
        if self._original_response and hasattr(self._original_response, '__aenter__'):
            await self._original_response.__aenter__()
        return self
    
    async def __aexit__(self, *args):
        # 원본 response가 async context manager를 지원하면 사용
        if self._original_response and hasattr(self._original_response, '__aexit__'):
            return await self._original_response.__aexit__(*args)
        return False


class ResponsesStreamWrapper:
    """Responses API 스트림을 래핑하는 클래스"""
    
    def __init__(self, stream_manager, client, request_params, start_time, parent_execution_id=None):
        self._stream_manager = stream_manager
        self._client = client
        self._request_params = request_params
        self._start_time = start_time
        self._parent_execution_id = parent_execution_id
        self._collected_text = ""
        self._final_response = None
        self._entered = False
        self._stream = None  # The actual ResponseStream returned by __enter__
    
    def __getattr__(self, name):
        """알 수 없는 속성은 실제 stream 또는 stream_manager로 위임합니다."""
        if name.startswith('_'):
            raise AttributeError(name)
        # If we've entered the context, delegate to the actual stream
        if self._stream is not None:
            return getattr(self._stream, name)
        return getattr(self._stream_manager, name)
    
    def __enter__(self):
        # __enter__ returns the actual ResponseStream object
        self._stream = self._stream_manager.__enter__()
        self._entered = True
        return self
    
    def __exit__(self, *args):
        result = self._stream_manager.__exit__(*args)
        self._finalize_trace()
        return result
    
    async def __aenter__(self):
        # __aenter__ returns the actual AsyncResponseStream object
        self._stream = await self._stream_manager.__aenter__()
        self._entered = True
        return self
    
    async def __aexit__(self, *args):
        result = await self._stream_manager.__aexit__(*args)
        self._finalize_trace()
        return result
    
    def until_done(self):
        """이벤트를 순회하며 텍스트를 수집합니다."""
        if self._stream is None:
            raise RuntimeError("Stream not entered. Use 'with' statement.")
        for event in self._stream.until_done():
            # 텍스트 델타 수집
            if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                if hasattr(event, 'delta'):
                    self._collected_text += event.delta
            yield event
    
    async def until_done_async(self):
        """비동기로 이벤트를 순회하며 텍스트를 수집합니다."""
        if self._stream is None:
            raise RuntimeError("Stream not entered. Use 'async with' statement.")
        async for event in self._stream.until_done():
            # 텍스트 델타 수집
            if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                if hasattr(event, 'delta'):
                    self._collected_text += event.delta
            yield event
    
    def get_final_response(self):
        """최종 응답을 가져옵니다."""
        if self._stream is None:
            raise RuntimeError("Stream not entered. Use 'with' statement.")
        self._final_response = self._stream.get_final_response()
        return self._final_response
    
    def close(self):
        """스트림을 닫습니다."""
        if self._stream is not None:
            return self._stream.close()
        return self._stream_manager.close()
    
    def _finalize_trace(self):
        """스트리밍 완료 후 trace를 기록합니다."""
        import time
        
        end_time = time.time()
        
        # 최종 응답에서 데이터 추출
        usage = None
        finish_reason = None
        
        if self._final_response:
            usage = extract_detailed_usage(self._final_response)
            # Responses API는 status 필드 사용
            status = getattr(self._final_response, 'status', None)
            if status:
                status_map = {
                    "completed": "stop",
                    "incomplete": "length",
                    "failed": "error",
                }
                finish_reason = status_map.get(status, status)
            
            # output_text가 있으면 사용
            if not self._collected_text and hasattr(self._final_response, 'output_text'):
                self._collected_text = self._final_response.output_text or ""
        
        trace_data = {
            "provider": "openai",
            "model": self._request_params.get("model", "unknown"),
            "prompt": format_messages(self._request_params.get("input", [])),
            "response": self._collected_text,
            "start_time": self._start_time,
            "end_time": end_time,
            "finish_reason": finish_reason,
            "metadata": {
                "request": {
                    "parameters": {
                        k: v
                        for k, v in self._request_params.items()
                        if k not in ["input", "model", "prompt"] and v is not None
                    },
                    "input": self._request_params.get("input", []),
                },
                "response": {
                    "streaming": True,
                    "usage": usage,
                    "finish_reason": finish_reason,
                },
            },
        }
        
        if usage:
            trace_data["tokens_used"] = usage.get("total_tokens")
        
        if self._parent_execution_id:
            trace_data["execution_parent_id"] = self._parent_execution_id
        
        self._client._trace_method(**trace_data)


def wrap_responses_stream(stream_manager, client, request_params, start_time, is_async: bool, parent_execution_id=None):
    """
    Responses API 스트림 매니저를 래핑합니다.
    
    Args:
        stream_manager: OpenAI Responses API 스트림 매니저
        client: Nora client 인스턴스
        request_params: 요청 파라미터
        start_time: 시작 시간
        is_async: 비동기 여부
        parent_execution_id: 부모 execution span ID (optional)
        
    Returns:
        래핑된 스트림 매니저
    """
    return ResponsesStreamWrapper(
        stream_manager, client, request_params, start_time, parent_execution_id
    )


def wrap_streaming_response(response, client, request_params, start_time, is_async: bool, parent_execution_id=None):
    """
    스트리밍 응답을 래핑하여 완료 시 trace를 기록합니다.

    Args:
        response: OpenAI 스트리밍 응답
        client: Nora client 인스턴스
        request_params: 요청 파라미터
        start_time: 시작 시간
        is_async: 비동기 여부
        parent_execution_id: 부모 execution span ID (optional)

    Returns:
        래핑된 스트리밍 응답
    """
    # 스트리밍 데이터 수집용
    collected_data = {
        "chunks": [],
        "text": "",
        "tool_calls": {},
        "finish_reason": None,
        "usage": None,
    }

    def process_chunk(chunk):
        """청크를 처리하고 데이터를 수집합니다."""
        try:
            # Usage 정보 추출 (stream_options: {"include_usage": True}일 때)
            # 이 경우 마지막 청크에만 usage가 있고 choices는 비어있을 수 있음
            if hasattr(chunk, "usage") and chunk.usage:
                collected_data["usage"] = extract_detailed_usage(chunk)

            # Choices가 있는 경우 (텍스트/tool_call 데이터)
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]

                # 텍스트 델타
                if hasattr(choice, "delta"):
                    delta = choice.delta
                    if hasattr(delta, "content") and delta.content:
                        collected_data["text"] += delta.content

                    # Tool call 델타
                    if hasattr(delta, "tool_calls") and delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in collected_data["tool_calls"]:
                                collected_data["tool_calls"][idx] = {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }

                            if hasattr(tc_delta, "id") and tc_delta.id:
                                collected_data["tool_calls"][idx]["id"] = tc_delta.id
                            if hasattr(tc_delta, "function"):
                                func = tc_delta.function
                                if hasattr(func, "name") and func.name:
                                    collected_data["tool_calls"][idx]["function"][
                                        "name"
                                    ] = func.name
                                if hasattr(func, "arguments") and func.arguments:
                                    collected_data["tool_calls"][idx]["function"][
                                        "arguments"
                                    ] += func.arguments

                # Finish reason
                if hasattr(choice, "finish_reason") and choice.finish_reason:
                    collected_data["finish_reason"] = choice.finish_reason

        except Exception:
            pass

        return chunk

    def finalize_trace():
        """스트리밍 완료 후 trace를 기록합니다."""
        import time

        end_time = time.time()

        # Tool calls를 리스트로 변환
        tool_calls_list = None
        if collected_data["tool_calls"]:
            tool_calls_list = [
                collected_data["tool_calls"][idx]
                for idx in sorted(collected_data["tool_calls"].keys())
            ]

        trace_data = {
            "provider": "openai",
            "model": request_params["model"],
            "prompt": format_messages(request_params.get("messages", [])),
            "response": collected_data["text"],
            "start_time": start_time,
            "end_time": end_time,
            "finish_reason": collected_data["finish_reason"],
            "metadata": {
                "request": {
                    "parameters": {
                        k: v
                        for k, v in request_params.items()
                        if k not in ["messages", "model", "prompt"] and v is not None
                    }
                },
                "response": {
                    "streaming": True,
                    "chunks_count": len(collected_data["chunks"]),
                    "usage": collected_data["usage"],
                    "finish_reason": collected_data["finish_reason"],
                },
            },
        }

        trace_data["metadata"]["request"]["messages"] = request_params.get("messages", [])

        if tool_calls_list:
            trace_data["tool_calls"] = tool_calls_list
            trace_data["metadata"]["response"]["tool_calls"] = tool_calls_list

        if collected_data["usage"]:
            trace_data["tokens_used"] = collected_data["usage"].get("total_tokens")

        # Add parent execution ID if exists
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id

        client._trace_method(**trace_data)

    # 동기 스트리밍 래퍼
    if not is_async:

        def sync_wrapper():
            try:
                for chunk in response:
                    collected_data["chunks"].append(chunk)
                    yield process_chunk(chunk)
            finally:
                finalize_trace()

        return StreamWrapper(sync_wrapper(), response)

    # 비동기 스트리밍 래퍼
    else:

        async def async_wrapper():
            try:
                async for chunk in response:
                    collected_data["chunks"].append(chunk)
                    yield process_chunk(chunk)
            finally:
                finalize_trace()

        return StreamWrapper(async_wrapper(), response)
