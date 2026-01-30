"""
Ollama 스트리밍 응답 처리
"""

import time
from datetime import datetime
from typing import Any, Optional
from ...client import _current_execution_span
from .metadata_builder import build_trace_data
from .types import RequestParams


class OllamaStreamingWrapper:
    """
    Ollama 스트리밍 응답을 래핑하여 trace 데이터를 수집합니다.
    """
    
    def __init__(
        self,
        stream,
        client,
        request_params: RequestParams,
        start_time: float,
        is_async: bool = False,
        parent_execution_id: Optional[str] = None,
    ):
        self._stream = stream
        self._client = client
        self._request_params = request_params
        self._start_time = start_time
        self._is_async = is_async
        self._parent_execution_id = parent_execution_id
        
        # 수집된 데이터
        self._collected_text = ""
        self._tool_calls = None
        self._final_chunk = None
        
        # Execution span 설정
        span_data = {
            "id": None,  # Will be set after trace creation
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._span_token = _current_execution_span.set(span_data)
        self._span_data = span_data
    
    def __iter__(self):
        """동기 스트리밍 iteration"""
        if self._is_async:
            raise RuntimeError("Use 'async for' with async streams")
        
        try:
            for chunk in self._stream:
                self._process_chunk(chunk)
                yield chunk
            
            # 스트리밍 완료 후 trace 전송
            self._finalize_trace()
        finally:
            _current_execution_span.reset(self._span_token)
    
    async def __aiter__(self):
        """비동기 스트리밍 iteration"""
        if not self._is_async:
            raise RuntimeError("Use 'for' with sync streams")
        
        try:
            async for chunk in self._stream:
                self._process_chunk(chunk)
                yield chunk
            
            # 스트리밍 완료 후 trace 전송
            self._finalize_trace()
        finally:
            _current_execution_span.reset(self._span_token)
    
    def _process_chunk(self, chunk: Any) -> None:
        """
        스트림 청크를 처리하여 데이터를 수집합니다.
        
        Args:
            chunk: Ollama 스트림 청크 (dict)
        """
        try:
            if isinstance(chunk, dict):
                # 메시지 내용 수집
                message = chunk.get("message", {})
                content = message.get("content", "")
                if content:
                    self._collected_text += content
                
                # Tool calls 수집
                if "tool_calls" in message and message["tool_calls"]:
                    if self._tool_calls is None:
                        self._tool_calls = []
                    self._tool_calls.extend(message["tool_calls"])
                
                # 마지막 청크 저장 (done=True인 청크에 토큰 정보 포함)
                if chunk.get("done", False):
                    self._final_chunk = chunk
            else:
                # Object with attributes
                if hasattr(chunk, "message"):
                    message = chunk.message
                    if isinstance(message, dict):
                        content = message.get("content", "")
                    elif hasattr(message, "content"):
                        content = str(message.content) if message.content else ""
                    else:
                        content = ""
                    
                    if content:
                        self._collected_text += content
                    
                    # Tool calls
                    if isinstance(message, dict) and "tool_calls" in message:
                        if self._tool_calls is None:
                            self._tool_calls = []
                        self._tool_calls.extend(message["tool_calls"])
                    elif hasattr(message, "tool_calls") and message.tool_calls:
                        if self._tool_calls is None:
                            self._tool_calls = []
                        self._tool_calls.extend(message.tool_calls)
                
                # 마지막 청크
                if hasattr(chunk, "done") and chunk.done:
                    self._final_chunk = chunk
        except Exception as e:
            # 청크 처리 중 오류가 발생해도 스트리밍은 계속
            pass
    
    def _finalize_trace(self) -> None:
        """스트리밍 완료 후 trace를 전송합니다."""
        end_time = time.time()
        
        # 가짜 응답 객체 생성 (build_trace_data가 사용할 수 있도록)
        fake_response = {
            "message": {
                "content": self._collected_text,
            },
            "done": True,
        }
        
        # Tool calls 추가
        if self._tool_calls:
            fake_response["message"]["tool_calls"] = self._tool_calls
        
        # 마지막 청크에서 토큰 정보 추출
        if self._final_chunk:
            if isinstance(self._final_chunk, dict):
                if "prompt_eval_count" in self._final_chunk:
                    fake_response["prompt_eval_count"] = self._final_chunk["prompt_eval_count"]
                if "eval_count" in self._final_chunk:
                    fake_response["eval_count"] = self._final_chunk["eval_count"]
                if "model" in self._final_chunk:
                    fake_response["model"] = self._final_chunk["model"]
                if "created_at" in self._final_chunk:
                    fake_response["created_at"] = self._final_chunk["created_at"]
            else:
                # Object attributes
                if hasattr(self._final_chunk, "prompt_eval_count"):
                    fake_response["prompt_eval_count"] = self._final_chunk.prompt_eval_count
                if hasattr(self._final_chunk, "eval_count"):
                    fake_response["eval_count"] = self._final_chunk.eval_count
                if hasattr(self._final_chunk, "model"):
                    fake_response["model"] = self._final_chunk.model
                if hasattr(self._final_chunk, "created_at"):
                    fake_response["created_at"] = self._final_chunk.created_at
        
        # Trace 데이터 생성
        trace_data = build_trace_data(
            self._request_params,
            fake_response,
            self._start_time,
            end_time,
            error=None,
        )
        
        # 부모 실행 ID 추가
        if self._parent_execution_id:
            trace_data["execution_parent_id"] = self._parent_execution_id
        
        # Execution span ID 업데이트
        self._span_data["id"] = trace_data.get("id")
        
        # Trace 전송
        self._client._trace_method(**trace_data)
    
    def __getattr__(self, name):
        """알 수 없는 속성은 원본 스트림으로 위임합니다."""
        return getattr(self._stream, name)
