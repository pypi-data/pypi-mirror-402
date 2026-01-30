"""
LiteLLM 요청/응답 유틸리티
"""
from typing import Any, Dict, List, Optional

from ..utils import format_messages, safe_extract_attr


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_request_params(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """LiteLLM 요청 파라미터를 정규화합니다."""
    return {
        "model": kwargs.get("model", "unknown"),
        "messages": kwargs.get("messages", []),
        "prompt": kwargs.get("prompt"),
        "temperature": kwargs.get("temperature"),
        "max_tokens": kwargs.get("max_tokens"),
        "top_p": kwargs.get("top_p"),
        "presence_penalty": kwargs.get("presence_penalty"),
        "frequency_penalty": kwargs.get("frequency_penalty"),
        "n": kwargs.get("n", 1),
        "stream": kwargs.get("stream", False),
        "stop": kwargs.get("stop"),
        "tools": kwargs.get("tools"),
        "tool_choice": kwargs.get("tool_choice"),
        "response_format": kwargs.get("response_format"),
        "metadata": kwargs.get("metadata"),
        "user": kwargs.get("user"),
    }


def extract_response_content(response: Any) -> Dict[str, Any]:
    """응답에서 텍스트와 tool_calls를 추출합니다."""
    text = ""
    tool_calls: Optional[List[Dict[str, Any]]] = None

    try:
        choices = _get(response, "choices", [])
        if choices:
            first = choices[0]
            message = _get(first, "message", {}) or {}

            # 텍스트
            msg_text = _get(message, "content") or _get(first, "content") or ""
            if isinstance(msg_text, list):
                msg_text = "".join(str(x) for x in msg_text if x)
            text = msg_text or ""

            # Tool calls
            raw_tool_calls = _get(message, "tool_calls", [])
            if raw_tool_calls:
                tool_calls = []
                for tc in raw_tool_calls:
                    tc_dict = tc.model_dump() if hasattr(tc, "model_dump") else tc.dict() if hasattr(tc, "dict") else tc
                    if not isinstance(tc_dict, dict):
                        continue
                    tool_calls.append(
                        {
                            "id": tc_dict.get("id", ""),
                            "type": tc_dict.get("type", "function"),
                            "function": {
                                "name": tc_dict.get("function", {}).get("name", ""),
                                "arguments": tc_dict.get("function", {}).get("arguments", ""),
                            },
                        }
                    )
    except Exception:
        pass

    return {"text": text, "tool_calls": tool_calls}


def extract_finish_reason(response: Any) -> Optional[str]:
    try:
        choices = _get(response, "choices", [])
        if choices:
            return _get(choices[0], "finish_reason")
    except Exception:
        return None
    return None


def extract_usage(response: Any) -> Dict[str, Any]:
    usage = {}
    try:
        usage_obj = _get(response, "usage", None)
        if usage_obj:
            usage = {
                "prompt_tokens": safe_extract_attr(usage_obj, "prompt_tokens", default=0),
                "completion_tokens": safe_extract_attr(usage_obj, "completion_tokens", default=0),
                "total_tokens": safe_extract_attr(usage_obj, "total_tokens", default=0),
            }
    except Exception:
        pass
    return usage


def format_prompt_from_params(request_params: Dict[str, Any]) -> str:
    messages = request_params.get("messages") or []
    prompt = request_params.get("prompt")
    if messages:
        return format_messages(messages)
    if isinstance(prompt, str):
        return prompt
    return ""
