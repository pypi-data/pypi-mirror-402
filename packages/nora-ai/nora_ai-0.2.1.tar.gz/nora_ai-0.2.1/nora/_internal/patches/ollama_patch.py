"""
Ollama 라이브러리 자동 패치
Ollama API 호출 및 OpenAI SDK를 통한 Ollama 호출을 자동으로 trace합니다.
"""

import time
from datetime import datetime
from typing import Any, Callable, Dict

from ...client import _get_active_client as get_active_client, _current_execution_span
from ..._internal.ollama import (
    extract_request_params,
    build_trace_data,
    wrap_streaming_response,
)


def patch_ollama() -> None:
    """
    Ollama 라이브러리를 패치하여 자동 trace를 활성화합니다.
    Ollama SDK와 OpenAI SDK(base_url 변경) 둘 다 지원합니다.
    """
    _patch_ollama_sdk()
    _patch_openai_for_ollama()


def _patch_ollama_sdk() -> None:
    """Ollama SDK를 패치합니다."""
    try:
        import ollama
    except ImportError:
        return
    
    if hasattr(ollama, "_nora_patched"):
        return
    
    # Ollama Client 클래스 패치
    try:
        from ollama import Client, AsyncClient
        
        # 원본 메서드 저장
        original_sync_chat = Client.chat
        original_async_chat = AsyncClient.chat
        
        # 패치된 메서드로 교체
        Client.chat = _create_patched_method(original_sync_chat, is_async=False)
        AsyncClient.chat = _create_patched_method(original_async_chat, is_async=True)
    except (ImportError, AttributeError):
        pass
    
    # 모듈 레벨 함수 패치 (ollama.chat() 직접 호출)
    if hasattr(ollama, "chat"):
        original_chat = ollama.chat
        ollama.chat = _create_patched_function(original_chat, is_async=False)
    
    ollama._nora_patched = True


def _patch_openai_for_ollama() -> None:
    """
    OpenAI SDK를 통한 Ollama 사용을 감지하고 패치합니다.
    base_url이 localhost:11434를 포함하면 Ollama로 인식합니다.
    
    Note: 이미 openai_patch.py에서 OpenAI가 패치되었으므로,
    여기서는 추가 패치 없이 응답 메타데이터에서 Ollama 여부만 확인합니다.
    """
    # OpenAI SDK는 이미 openai_patch.py에서 패치됨
    # base_url 확인은 metadata_builder에서 수행
    pass


def _create_patched_method(original_method: Callable, is_async: bool) -> Callable:
    """
    Ollama Client 메서드에 대한 패치된 함수를 생성합니다.
    
    Args:
        original_method: 원본 메서드
        is_async: 비동기 메서드 여부
        
    Returns:
        패치된 메서드
    """
    if is_async:
        async def patched_async_method(self, *args, **kwargs):
            return await _execute_with_trace_async(original_method, self, args, kwargs)
        return patched_async_method
    else:
        def patched_sync_method(self, *args, **kwargs):
            return _execute_with_trace_sync(original_method, self, args, kwargs)
        return patched_sync_method


def _create_patched_function(original_func: Callable, is_async: bool) -> Callable:
    """
    Ollama 모듈 레벨 함수에 대한 패치된 함수를 생성합니다.
    
    Args:
        original_func: 원본 함수
        is_async: 비동기 함수 여부
        
    Returns:
        패치된 함수
    """
    if is_async:
        async def patched_async(*args, **kwargs):
            return await _execute_with_trace_async(original_func, None, args, kwargs)
        return patched_async
    else:
        def patched_sync(*args, **kwargs):
            return _execute_with_trace_sync(original_func, None, args, kwargs)
        return patched_sync


def _execute_with_trace_sync(
    original_func: Callable,
    self: Any,
    args: tuple,
    kwargs: Dict[str, Any],
) -> Any:
    """
    동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.
    
    Args:
        original_func: 원본 함수
        self: 함수의 self 인자 (메서드인 경우)
        args: 위치 인자
        kwargs: 키워드 인자
        
    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        if self is not None:
            return original_func(self, *args, **kwargs)
        else:
            return original_func(*args, **kwargs)
    
    start_time = time.time()
    request_params = extract_request_params(kwargs)
    
    # Get parent execution span (if exists)
    parent_span = _current_execution_span.get()
    parent_execution_id = parent_span.get("id") if parent_span else None
    
    # Create execution span context placeholder
    span_data = {
        "id": None,  # Will be set after trace creation
        "timestamp": datetime.utcnow().isoformat(),
    }
    token = _current_execution_span.set(span_data)
    
    try:
        # Execute original function
        if self is not None:
            response = original_func(self, *args, **kwargs)
        else:
            response = original_func(*args, **kwargs)
        
        end_time = time.time()
        
        # 스트리밍 처리
        if kwargs.get("stream", False):
            return wrap_streaming_response(
                response, client, request_params, start_time,
                is_async=False, parent_execution_id=parent_execution_id
            )
        
        # 일반 응답 처리
        trace_data = build_trace_data(request_params, response, start_time, end_time, error=None)
        
        # Add parent execution ID if exists
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id
            if parent_span and "name" in parent_span:
                trace_data["parent_function_name"] = parent_span["name"]
        
        # Update execution span context with the actual trace ID
        span_data["id"] = trace_data.get("id")
        
        # Send trace
        client._trace_method(**trace_data)
        
        return response
    
    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        
        # Add parent execution ID if exists
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id
            if parent_span and "name" in parent_span:
                trace_data["parent_function_name"] = parent_span["name"]
        
        # Update execution span context with the actual trace ID
        span_data["id"] = trace_data.get("id")
        
        # Send trace
        client._trace_method(**trace_data)
        raise
    finally:
        _current_execution_span.reset(token)


async def _execute_with_trace_async(
    original_func: Callable,
    self: Any,
    args: tuple,
    kwargs: Dict[str, Any],
) -> Any:
    """
    비동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.
    
    Args:
        original_func: 원본 함수
        self: 함수의 self 인자 (메서드인 경우)
        args: 위치 인자
        kwargs: 키워드 인자
        
    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        if self is not None:
            return await original_func(self, *args, **kwargs)
        else:
            return await original_func(*args, **kwargs)
    
    start_time = time.time()
    request_params = extract_request_params(kwargs)
    
    # Get parent execution span (if exists)
    parent_span = _current_execution_span.get()
    parent_execution_id = parent_span.get("id") if parent_span else None
    
    # Create execution span context placeholder
    span_data = {
        "id": None,  # Will be set after trace creation
        "timestamp": datetime.utcnow().isoformat(),
    }
    token = _current_execution_span.set(span_data)
    
    try:
        # Execute original function
        if self is not None:
            response = await original_func(self, *args, **kwargs)
        else:
            response = await original_func(*args, **kwargs)
        
        end_time = time.time()
        
        # 스트리밍 처리
        if kwargs.get("stream", False):
            return wrap_streaming_response(
                response, client, request_params, start_time,
                is_async=True, parent_execution_id=parent_execution_id
            )
        
        # 일반 응답 처리
        trace_data = build_trace_data(request_params, response, start_time, end_time, error=None)
        
        # Add parent execution ID if exists
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id
            if parent_span and "name" in parent_span:
                trace_data["parent_function_name"] = parent_span["name"]
        
        # Update execution span context with the actual trace ID
        span_data["id"] = trace_data.get("id")
        
        # Send trace
        client._trace_method(**trace_data)
        
        return response
    
    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        
        # Add parent execution ID if exists
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id
            if parent_span and "name" in parent_span:
                trace_data["parent_function_name"] = parent_span["name"]
        
        # Update execution span context with the actual trace ID
        span_data["id"] = trace_data.get("id")
        
        # Send trace
        client._trace_method(**trace_data)
        raise
    finally:
        _current_execution_span.reset(token)
