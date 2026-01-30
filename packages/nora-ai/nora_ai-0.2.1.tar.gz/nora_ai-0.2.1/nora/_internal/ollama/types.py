"""
Ollama API 타입 정의
"""

from typing import TypedDict, Optional, List, Dict, Any


class RequestParams(TypedDict, total=False):
    """Ollama 요청 파라미터"""
    model: str
    messages: List[Dict[str, str]]
    stream: bool
    format: Optional[str]
    options: Optional[Dict[str, Any]]
    keep_alive: Optional[str]
    tools: Optional[List[Dict[str, Any]]]


class ResponseContent(TypedDict, total=False):
    """Ollama 응답 내용"""
    text: str
    tool_calls: Optional[List[Dict[str, Any]]]


class UsageInfo(TypedDict, total=False):
    """Ollama 토큰 사용량 정보"""
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
