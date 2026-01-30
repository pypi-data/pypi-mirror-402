"""
Ollama API 응답/요청 처리 유틸리티
"""

from typing import Any, Dict, Optional, List
from ..._internal.utils import safe_extract_attr, format_messages
from .types import RequestParams, ResponseContent, UsageInfo
from .token_estimator import estimate_tokens, estimate_messages_tokens


def extract_request_params(kwargs: Dict[str, Any]) -> RequestParams:
    """
    Ollama 요청 파라미터를 추출합니다.
    
    Args:
        kwargs: API 호출 키워드 인자
        
    Returns:
        추출된 요청 파라미터
    """
    return RequestParams(
        model=kwargs.get("model", "unknown"),
        messages=kwargs.get("messages", []),
        stream=kwargs.get("stream", False),
        format=kwargs.get("format"),
        options=kwargs.get("options"),
        keep_alive=kwargs.get("keep_alive"),
        tools=kwargs.get("tools"),
    )


def format_prompt(request_params: RequestParams) -> str:
    """
    요청 파라미터에서 prompt를 추출합니다.
    
    Args:
        request_params: 요청 파라미터
        
    Returns:
        포맷된 prompt 문자열
    """
    return format_messages(request_params.get("messages", []))


def extract_response_content(response: Any) -> ResponseContent:
    """
    Ollama 응답에서 텍스트와 tool calls를 추출합니다.
    
    Args:
        response: Ollama API 응답 객체
        
    Returns:
        추출된 응답 내용
    """
    result = ResponseContent(
        text="",
        tool_calls=None,
    )
    
    try:
        # Ollama response is a dict-like object
        if isinstance(response, dict):
            message = response.get("message", {})
            result["text"] = message.get("content", "")
            
            # Tool calls if present
            if "tool_calls" in message and message["tool_calls"]:
                result["tool_calls"] = message["tool_calls"]
        else:
            # Object with attributes
            if hasattr(response, "message"):
                message = response.message
                if isinstance(message, dict):
                    result["text"] = message.get("content", "")
                    if "tool_calls" in message and message["tool_calls"]:
                        result["tool_calls"] = message["tool_calls"]
                elif hasattr(message, "content"):
                    result["text"] = str(message.content) if message.content else ""
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        result["tool_calls"] = message.tool_calls
    except Exception as e:
        # Fallback to string representation
        result["text"] = str(response) if response else ""
    
    return result


def extract_detailed_usage(response: Any, request_params: Optional[RequestParams] = None) -> UsageInfo:
    """
    Ollama 응답에서 토큰 사용량을 추출하거나 추정합니다.
    
    Args:
        response: Ollama API 응답 객체
        request_params: 요청 파라미터 (토큰 추정용)
        
    Returns:
        토큰 사용량 정보
    """
    usage = UsageInfo(
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
    )
    
    try:
        # Ollama는 prompt_eval_count, eval_count 필드로 토큰 수 제공
        if isinstance(response, dict):
            prompt_tokens = response.get("prompt_eval_count")
            completion_tokens = response.get("eval_count")
            
            if prompt_tokens is not None:
                usage["prompt_tokens"] = prompt_tokens
            if completion_tokens is not None:
                usage["completion_tokens"] = completion_tokens
            if prompt_tokens is not None and completion_tokens is not None:
                usage["total_tokens"] = prompt_tokens + completion_tokens
        else:
            # Object attributes
            prompt_tokens = safe_extract_attr(response, "prompt_eval_count")
            completion_tokens = safe_extract_attr(response, "eval_count")
            
            if prompt_tokens is not None:
                usage["prompt_tokens"] = prompt_tokens
            if completion_tokens is not None:
                usage["completion_tokens"] = completion_tokens
            if prompt_tokens is not None and completion_tokens is not None:
                usage["total_tokens"] = prompt_tokens + completion_tokens
    except Exception:
        pass
    
    # If no token counts available, estimate using tiktoken
    if usage["total_tokens"] is None and request_params is not None:
        try:
            # Estimate prompt tokens from messages
            messages = request_params.get("messages", [])
            if messages:
                estimated_prompt = estimate_messages_tokens(messages)
                usage["prompt_tokens"] = estimated_prompt
            
            # Estimate completion tokens from response
            response_content = extract_response_content(response)
            response_text = response_content.get("text", "")
            if response_text:
                estimated_completion = estimate_tokens(response_text)
                usage["completion_tokens"] = estimated_completion
            
            # Calculate total
            if usage["prompt_tokens"] is not None and usage["completion_tokens"] is not None:
                usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        except Exception:
            pass
    
    return usage


def extract_finish_reason(response: Any) -> Optional[str]:
    """
    Ollama 응답에서 완료 이유를 추출합니다.
    
    Args:
        response: Ollama API 응답 객체
        
    Returns:
        완료 이유 (있는 경우)
    """
    try:
        if isinstance(response, dict):
            # done_reason 필드 확인
            if "done_reason" in response:
                return response["done_reason"]
            # done 필드만 있는 경우
            if response.get("done", False):
                return "stop"
        else:
            # Object attributes
            done_reason = safe_extract_attr(response, "done_reason")
            if done_reason:
                return done_reason
            done = safe_extract_attr(response, "done")
            if done:
                return "stop"
    except Exception:
        pass
    
    return None


def wrap_streaming_response(
    stream,
    client,
    request_params: RequestParams,
    start_time: float,
    is_async: bool = False,
    parent_execution_id: Optional[str] = None,
):
    """
    Ollama 스트리밍 응답을 래핑하여 trace 데이터를 수집합니다.
    
    Args:
        stream: 원본 스트림
        client: Nora 클라이언트
        request_params: 요청 파라미터
        start_time: 시작 시간
        is_async: 비동기 스트림 여부
        parent_execution_id: 부모 실행 ID
        
    Returns:
        래핑된 스트림
    """
    from .streaming import OllamaStreamingWrapper
    
    return OllamaStreamingWrapper(
        stream,
        client,
        request_params,
        start_time,
        is_async=is_async,
        parent_execution_id=parent_execution_id,
    )
