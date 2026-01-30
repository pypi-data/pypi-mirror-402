"""
Ollama Trace 메타데이터 구성
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from ..._internal.utils import safe_extract_attr
from .types import RequestParams, ResponseContent, UsageInfo
from .utils import (
    format_prompt,
    extract_response_content,
    extract_detailed_usage,
    extract_finish_reason,
)


def build_trace_data(
    request_params: RequestParams,
    response: Any,
    start_time: float,
    end_time: float,
    error: Optional[str],
) -> Dict[str, Any]:
    """
    완전한 trace 데이터를 구성합니다.
    
    Args:
        request_params: 요청 파라미터
        response: API 응답
        start_time: 시작 시간
        end_time: 종료 시간
        error: 에러 메시지 (있는 경우)
        
    Returns:
        Trace 데이터 dictionary
    """
    # Use model as name for agent resolution
    model_name = request_params.get("model", "ollama_llm")
    
    trace_data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "provider": "ollama",
        "model": model_name,
        "name": model_name,  # Add name field for agent_name resolution
        "start_time": start_time,
        "end_time": end_time,
        "prompt": format_prompt(request_params),
    }
    
    if response and not error:
        _add_response_data(trace_data, response, request_params)
    else:
        _add_error_data(trace_data, error, request_params)
    
    return trace_data


def _add_response_data(
    trace_data: Dict[str, Any], response: Any, request_params: RequestParams
) -> None:
    """응답 데이터를 trace_data에 추가합니다."""
    # 응답 내용 추출
    response_content = extract_response_content(response)
    trace_data["response"] = response_content["text"]
    
    # 토큰 사용량 (실제 값 또는 추정값)
    usage = extract_detailed_usage(response, request_params)
    trace_data["tokens_used"] = usage.get("total_tokens")
    
    # 완료 이유
    finish_reason = extract_finish_reason(response)
    if finish_reason:
        trace_data["finish_reason"] = finish_reason
    
    # Tool calls 추출 (selected_option 용)
    tool_calls = response_content.get("tool_calls")
    if tool_calls:
        trace_data["selected_option"] = [
            {
                "name": tc.get("function", {}).get("name") if isinstance(tc, dict) else None,
                "type": "tool",
            }
            for tc in tool_calls
        ]
    
    # 메타데이터 구성
    metadata = {
        "request": {
            "model": request_params.get("model"),
            "messages": request_params.get("messages", []),
            "options": request_params.get("options"),
            "format": request_params.get("format"),
            "tools": request_params.get("tools"),
        },
        "response": {
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        },
    }
    
    # Add response model info if available
    if isinstance(response, dict):
        metadata["response"]["model"] = response.get("model")
        metadata["response"]["created_at"] = response.get("created_at")
        metadata["response"]["done"] = response.get("done")
    
    # Add tool calls to metadata
    if tool_calls:
        metadata["response"]["tool_calls"] = tool_calls
    
    trace_data["metadata"] = metadata


def _add_error_data(
    trace_data: Dict[str, Any], error: Optional[str], request_params: RequestParams
) -> None:
    """에러 데이터를 trace_data에 추가합니다."""
    trace_data["response"] = f"Error: {error}" if error else "Error occurred"
    trace_data["tokens_used"] = None
    trace_data["error"] = error
    
    # 메타데이터 구성
    metadata = {
        "request": {
            "model": request_params.get("model"),
            "messages": request_params.get("messages", []),
            "options": request_params.get("options"),
            "format": request_params.get("format"),
            "tools": request_params.get("tools"),
        },
        "error": error,
    }
    
    trace_data["metadata"] = metadata
