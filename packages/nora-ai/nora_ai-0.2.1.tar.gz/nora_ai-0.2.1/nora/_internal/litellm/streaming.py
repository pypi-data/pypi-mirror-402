"""
LiteLLM 스트리밍 응답 처리
"""
from typing import Any, Dict

from .utils import format_prompt_from_params


class StreamWrapper:
    """Generator를 context manager로 감싸는 wrapper"""

    def __init__(self, generator, original_response=None):
        self._generator = generator
        self._original_response = original_response

    def __iter__(self):
        return self._generator

    def __aiter__(self):
        return self._generator

    def __enter__(self):
        if self._original_response and hasattr(self._original_response, "__enter__"):
            self._original_response.__enter__()
        return self

    def __exit__(self, *args):
        if self._original_response and hasattr(self._original_response, "__exit__"):
            return self._original_response.__exit__(*args)
        return False

    async def __aenter__(self):
        if self._original_response and hasattr(self._original_response, "__aenter__"):
            await self._original_response.__aenter__()
        return self

    async def __aexit__(self, *args):
        if self._original_response and hasattr(self._original_response, "__aexit__"):
            return await self._original_response.__aexit__(*args)
        return False


def _get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def wrap_streaming_response(response, client, request_params: Dict[str, Any], start_time: float, is_async: bool, parent_execution_id=None):
    """스트리밍 응답을 래핑하여 완료 시 trace를 기록합니다."""
    collected = {
        "chunks": [],
        "text": "",
        "tool_calls": {},
        "finish_reason": None,
        "usage": None,
    }

    def process_chunk(chunk):
        try:
            usage = _get(chunk, "usage")
            if usage:
                collected["usage"] = {
                    "prompt_tokens": _get(usage, "prompt_tokens", 0),
                    "completion_tokens": _get(usage, "completion_tokens", 0),
                    "total_tokens": _get(usage, "total_tokens", 0),
                }

            choices = _get(chunk, "choices", [])
            if choices:
                first = choices[0]
                delta = _get(first, "delta") or {}
                if isinstance(delta, dict):
                    content = delta.get("content")
                    if content:
                        collected["text"] += content
                    tool_deltas = delta.get("tool_calls") or []
                else:
                    content = _get(delta, "content")
                    if content:
                        collected["text"] += content
                    tool_deltas = _get(delta, "tool_calls", []) or []

                for tc_delta in tool_deltas:
                    idx = _get(tc_delta, "index", 0)
                    if idx not in collected["tool_calls"]:
                        collected["tool_calls"][idx] = {
                            "id": _get(tc_delta, "id", ""),
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    func = _get(tc_delta, "function", {}) or {}
                    name = _get(func, "name")
                    if name:
                        collected["tool_calls"][idx]["function"]["name"] = name
                    args = _get(func, "arguments")
                    if args:
                        collected["tool_calls"][idx]["function"]["arguments"] += str(args)

                fr = _get(first, "finish_reason") or _get(delta, "finish_reason")
                if fr:
                    collected["finish_reason"] = fr
        except Exception:
            pass
        return chunk

    def finalize_trace():
        import time

        end_time = time.time()
        tool_calls_list = None
        if collected["tool_calls"]:
            tool_calls_list = [collected["tool_calls"][idx] for idx in sorted(collected["tool_calls"].keys())]

        trace_data = {
            "provider": "litellm",
            "model": request_params.get("model", "unknown"),
            "prompt": format_prompt_from_params(request_params),
            "response": collected["text"],
            "start_time": start_time,
            "end_time": end_time,
            "finish_reason": collected["finish_reason"],
            "metadata": {
                "request": {
                    "parameters": {
                        k: v
                        for k, v in request_params.items()
                        if k not in ["messages", "prompt", "model"] and v is not None
                    },
                    "messages": request_params.get("messages", []),
                    "prompt": request_params.get("prompt"),
                },
                "response": {
                    "streaming": True,
                    "chunks_count": len(collected["chunks"]),
                    "usage": collected["usage"],
                    "finish_reason": collected["finish_reason"],
                },
            },
        }

        if tool_calls_list:
            trace_data["tool_calls"] = tool_calls_list
            trace_data["metadata"]["response"]["tool_calls"] = tool_calls_list

        if collected["usage"]:
            trace_data["tokens_used"] = collected["usage"].get("total_tokens")

        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id

        client._trace_method(**trace_data)

    if not is_async:

        def sync_wrapper():
            try:
                for chunk in response:
                    collected["chunks"].append(chunk)
                    yield process_chunk(chunk)
            finally:
                finalize_trace()

        return StreamWrapper(sync_wrapper(), response)

    async def async_wrapper():
        try:
            async for chunk in response:
                collected["chunks"].append(chunk)
                yield process_chunk(chunk)
        finally:
            finalize_trace()

    return StreamWrapper(async_wrapper(), response)
