"""
LiteLLM(litellm) 라이브러리 자동 패치
"""

import time
from datetime import datetime
from typing import Any, Callable, Dict

from ...client import _get_active_client as get_active_client, _current_execution_span
from ..._internal.litellm import extract_request_params, build_trace_data, wrap_streaming_response
from ..._internal.openai import auto_trace_tool_calls_from_response, auto_trace_tool_executions


def patch_litellm() -> None:
    """litellm.completion/acompletion을 패치하여 자동 trace를 활성화합니다."""
    try:
        import litellm
    except ImportError:
        return

    if hasattr(litellm, "_nora_patched"):
        return

    original_completion = getattr(litellm, "completion", None)
    original_acompletion = getattr(litellm, "acompletion", None)

    if original_completion:
        litellm.completion = _create_patched_function(original_completion, is_async=False)
    if original_acompletion:
        litellm.acompletion = _create_patched_function(original_acompletion, is_async=True)

    litellm._nora_patched = True


def _create_patched_function(original_func: Callable, is_async: bool) -> Callable:
    if is_async:

        async def patched_async(*args, **kwargs):
            return await _execute_with_trace_async(original_func, args, kwargs)

        return patched_async

    def patched_sync(*args, **kwargs):
        return _execute_with_trace_sync(original_func, args, kwargs)

    return patched_sync


def _execute_with_trace_sync(original_func: Callable, args: tuple, kwargs: Dict[str, Any]) -> Any:
    client = get_active_client()
    if not client or not client.enabled:
        return original_func(*args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs)

    parent_span = _current_execution_span.get()
    parent_execution_id = parent_span.get("id") if parent_span else None

    span_data = {"id": None, "timestamp": datetime.utcnow().isoformat()}
    token = _current_execution_span.set(span_data)

    try:
        response = original_func(*args, **kwargs)
        end_time = time.time()

        if request_params.get("stream"):
            return wrap_streaming_response(
                response,
                client,
                request_params,
                start_time,
                is_async=False,
                parent_execution_id=parent_execution_id,
            )

        trace_data = build_trace_data(request_params, response, start_time, end_time)
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id

        span_data["id"] = trace_data.get("id")

        auto_trace_tool_calls_from_response(response, client, trace_data.get("id"))
        auto_trace_tool_executions(request_params, client)

        client._trace_method(**trace_data)
        return response
    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id
        span_data["id"] = trace_data.get("id")

        auto_trace_tool_executions(request_params, client)

        client._trace_method(**trace_data)
        raise
    finally:
        _current_execution_span.reset(token)


async def _execute_with_trace_async(original_func: Callable, args: tuple, kwargs: Dict[str, Any]) -> Any:
    client = get_active_client()
    if not client or not client.enabled:
        return await original_func(*args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs)

    parent_span = _current_execution_span.get()
    parent_execution_id = parent_span.get("id") if parent_span else None

    span_data = {"id": None, "timestamp": datetime.utcnow().isoformat()}
    token = _current_execution_span.set(span_data)

    try:
        response = await original_func(*args, **kwargs)
        end_time = time.time()

        if request_params.get("stream"):
            return wrap_streaming_response(
                response,
                client,
                request_params,
                start_time,
                is_async=True,
                parent_execution_id=parent_execution_id,
            )

        trace_data = build_trace_data(request_params, response, start_time, end_time)
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id

        span_data["id"] = trace_data.get("id")

        auto_trace_tool_calls_from_response(response, client, trace_data.get("id"))
        auto_trace_tool_executions(request_params, client)

        client._trace_method(**trace_data)
        return response
    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        if parent_execution_id:
            trace_data["execution_parent_id"] = parent_execution_id
        span_data["id"] = trace_data.get("id")

        auto_trace_tool_executions(request_params, client)

        client._trace_method(**trace_data)
        raise
    finally:
        _current_execution_span.reset(token)
