"""
LiteLLM trace 메타데이터 구성
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from .utils import (
    extract_response_content,
    extract_finish_reason,
    extract_usage,
    format_prompt_from_params,
)


def build_trace_data(
    request_params: Dict[str, Any],
    response: Any,
    start_time: float,
    end_time: float,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    trace_data: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "provider": "litellm",
        "model": request_params.get("model", "unknown"),
        "start_time": start_time,
        "end_time": end_time,
        "prompt": format_prompt_from_params(request_params),
    }

    if response is not None and error is None:
        _add_response_data(trace_data, response, request_params)
    else:
        _add_error_data(trace_data, error, request_params)

    return trace_data


def _add_response_data(trace_data: Dict[str, Any], response: Any, request_params: Dict[str, Any]) -> None:
    content = extract_response_content(response)
    usage = extract_usage(response)
    finish_reason = extract_finish_reason(response)

    trace_data["response"] = content.get("text", "")
    trace_data["finish_reason"] = finish_reason
    trace_data["tokens_used"] = usage.get("total_tokens")

    if content.get("tool_calls"):
        trace_data["tool_calls"] = content["tool_calls"]

    trace_data["metadata"] = {
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
            "usage": usage,
            "finish_reason": finish_reason,
        },
    }


def _add_error_data(trace_data: Dict[str, Any], error: Optional[str], request_params: Dict[str, Any]) -> None:
    trace_data["error"] = error
    trace_data["metadata"] = {
        "request": {
            "parameters": {
                k: v
                for k, v in request_params.items()
                if k not in ["messages", "prompt", "model"] and v is not None
            },
            "messages": request_params.get("messages", []),
            "prompt": request_params.get("prompt"),
        }
    }
