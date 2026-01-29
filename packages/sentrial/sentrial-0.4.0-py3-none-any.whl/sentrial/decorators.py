"""
Sentrial Decorators - Easy instrumentation for AI agents

Provides decorators for automatic tracking:
- @tool: Track custom tool/function calls
- @session: Create session boundaries around agent runs

Usage:
    from sentrial import tool, session, configure
    
    configure(api_key="sentrial_live_xxx")
    
    @tool("search")
    def search_web(query: str) -> str:
        # Automatically tracked!
        return results
    
    @session("my-agent")
    def run_agent(user_id: str, message: str):
        # Creates session, tracks all tools inside
        result = search_web(message)
        return result
"""

import time
import asyncio
import functools
import traceback
import contextvars
from typing import Any, Optional, Callable, TypeVar, Union, Dict, overload
from functools import wraps

from .client import SentrialClient, Interaction, _get_client

# Type variables for generic decorators
F = TypeVar('F', bound=Callable[..., Any])

# Context variables for async-safe session tracking
_session_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'sentrial_session_id', default=None
)
_client_context: contextvars.ContextVar[Optional[SentrialClient]] = contextvars.ContextVar(
    'sentrial_client', default=None
)
_interaction_context: contextvars.ContextVar[Optional[Interaction]] = contextvars.ContextVar(
    'sentrial_interaction', default=None
)


def get_current_session_id() -> Optional[str]:
    """Get the current session ID from context (async-safe)."""
    return _session_context.get()


def get_current_interaction() -> Optional[Interaction]:
    """Get the current interaction from context (async-safe)."""
    return _interaction_context.get()


def get_current_client() -> Optional[SentrialClient]:
    """Get the current client from context, or the default client."""
    client = _client_context.get()
    if client:
        return client
    try:
        return _get_client()
    except Exception:
        return None


# ============================================================================
# @tool Decorator
# ============================================================================

@overload
def tool(name: str) -> Callable[[F], F]: ...

@overload
def tool(func: F) -> F: ...

def tool(name_or_func: Union[str, Callable] = None, *, name: Optional[str] = None):
    """
    Decorator to automatically track a tool/function call.
    
    When the decorated function is called within a session context,
    it automatically tracks the call with input, output, duration, and errors.
    
    Args:
        name: Optional custom name for the tool (defaults to function name)
    
    Usage:
        @tool("web_search")
        def search(query: str) -> dict:
            return {"results": [...]}
        
        @tool  # Uses function name
        def calculate(expression: str) -> float:
            return eval(expression)
        
        @tool("async_fetch")
        async def fetch_data(url: str) -> str:
            async with httpx.AsyncClient() as client:
                return (await client.get(url)).text
    
    The tool automatically tracks:
        - tool_input: Function arguments
        - tool_output: Return value
        - duration: Execution time
        - errors: Any exceptions raised
    """
    # Handle both @tool and @tool("name") syntax
    if callable(name_or_func):
        # Called as @tool without parentheses
        func = name_or_func
        tool_name = func.__name__
        return _make_tool_wrapper(func, tool_name)
    else:
        # Called as @tool("name") or @tool(name="name")
        tool_name = name_or_func or name
        
        def decorator(func: F) -> F:
            actual_name = tool_name or func.__name__
            return _make_tool_wrapper(func, actual_name)
        
        return decorator


def _make_tool_wrapper(func: Callable, tool_name: str) -> Callable:
    """Create a wrapper that tracks the function as a tool call."""
    
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _track_tool_async(func, tool_name, args, kwargs)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _track_tool_sync(func, tool_name, args, kwargs)
        return sync_wrapper


def _track_tool_sync(func: Callable, tool_name: str, args: tuple, kwargs: dict) -> Any:
    """Track a synchronous tool call."""
    start_time = time.time()
    
    # Build input representation
    tool_input = _build_tool_input(func, args, kwargs)
    
    client = get_current_client()
    session_id = get_current_session_id()
    
    try:
        # Execute the function
        result = func(*args, **kwargs)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Track success
        if client and session_id:
            tool_output = _serialize_output(result)
            try:
                client.track_tool_call(
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=tool_output,
                    metadata={"duration_ms": duration_ms},
                )
            except Exception as e:
                import logging
                logging.warning(f"Sentrial: Failed to track tool {tool_name}: {e}")
        
        return result
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Track error
        if client and session_id:
            try:
                client.track_error(
                    session_id=session_id,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    tool_name=tool_name,
                    stack_trace=traceback.format_exc(),
                    metadata={"duration_ms": duration_ms},
                )
            except Exception:
                pass
        
        raise


async def _track_tool_async(func: Callable, tool_name: str, args: tuple, kwargs: dict) -> Any:
    """Track an asynchronous tool call."""
    start_time = time.time()
    
    tool_input = _build_tool_input(func, args, kwargs)
    
    client = get_current_client()
    session_id = get_current_session_id()
    
    try:
        result = await func(*args, **kwargs)
        duration_ms = int((time.time() - start_time) * 1000)
        
        if client and session_id:
            tool_output = _serialize_output(result)
            try:
                client.track_tool_call(
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=tool_output,
                    metadata={"duration_ms": duration_ms},
                )
            except Exception as e:
                import logging
                logging.warning(f"Sentrial: Failed to track tool {tool_name}: {e}")
        
        return result
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        if client and session_id:
            try:
                client.track_error(
                    session_id=session_id,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    tool_name=tool_name,
                    stack_trace=traceback.format_exc(),
                    metadata={"duration_ms": duration_ms},
                )
            except Exception:
                pass
        
        raise


def _build_tool_input(func: Callable, args: tuple, kwargs: dict) -> dict:
    """Build a serializable representation of function inputs."""
    import inspect
    
    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        
        result = {}
        for param_name, value in bound.arguments.items():
            result[param_name] = _serialize_value(value)
        return result
    except Exception:
        # Fallback: just return args/kwargs
        return {
            "args": [_serialize_value(a) for a in args],
            "kwargs": {k: _serialize_value(v) for k, v in kwargs.items()},
        }


def _serialize_value(value: Any) -> Any:
    """Serialize a value for JSON storage."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    elif isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    else:
        # Try to convert to string
        try:
            return str(value)[:1000]  # Truncate long strings
        except Exception:
            return f"<{type(value).__name__}>"


def _serialize_output(value: Any) -> dict:
    """Serialize function output for tracking."""
    if value is None:
        return {"result": None}
    elif isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    else:
        return {"result": _serialize_value(value)}


# ============================================================================
# @session Decorator
# ============================================================================

@overload
def session(agent_name: str) -> Callable[[F], F]: ...

@overload
def session(func: F) -> F: ...

def session(
    name_or_func: Union[str, Callable] = None,
    *,
    agent_name: Optional[str] = None,
    user_id_param: str = "user_id",
    input_param: str = "input",
    message_param: str = "message",
):
    """
    Decorator to create a session boundary around an agent function.
    
    Automatically:
    - Creates a session when the function is called
    - Sets up context for @tool and wrapped LLM calls
    - Captures input from function parameters
    - Captures output from return value
    - Completes the session when the function returns
    - Marks as failed if an exception is raised
    
    Args:
        agent_name: Name of the agent (defaults to function name)
        user_id_param: Name of the parameter containing user_id (default: "user_id")
        input_param: Name of the parameter containing user input (default: "input")
        message_param: Alternative name for input parameter (default: "message")
    
    Usage:
        @session("support-agent")
        def handle_support_request(user_id: str, message: str):
            # Session automatically created
            # All @tool calls and wrapped LLM calls are tracked
            response = process_request(message)
            return response  # Captured as output
        
        @session("async-agent")
        async def handle_async(user_id: str, input: str):
            response = await process_async(input)
            return response
    
    Note:
        The function MUST have a `user_id` parameter (or specify `user_id_param`).
        Input is extracted from `input`, `message`, or the first string parameter.
    """
    # Handle both @session and @session("name") syntax
    if callable(name_or_func):
        func = name_or_func
        actual_agent_name = func.__name__
        return _make_session_wrapper(
            func, actual_agent_name, user_id_param, input_param, message_param
        )
    else:
        actual_agent_name = name_or_func or agent_name
        
        def decorator(func: F) -> F:
            final_name = actual_agent_name or func.__name__
            return _make_session_wrapper(
                func, final_name, user_id_param, input_param, message_param
            )
        
        return decorator


def _make_session_wrapper(
    func: Callable,
    agent_name: str,
    user_id_param: str,
    input_param: str,
    message_param: str,
) -> Callable:
    """Create a wrapper that manages session lifecycle."""
    
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _run_in_session_async(
                func, agent_name, user_id_param, input_param, message_param, args, kwargs
            )
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _run_in_session_sync(
                func, agent_name, user_id_param, input_param, message_param, args, kwargs
            )
        return sync_wrapper


def _extract_params(
    func: Callable,
    args: tuple,
    kwargs: dict,
    user_id_param: str,
    input_param: str,
    message_param: str,
) -> tuple[str, Optional[str]]:
    """Extract user_id and input from function parameters."""
    import inspect
    
    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = bound.arguments
    except Exception:
        arguments = kwargs.copy()
    
    # Extract user_id
    user_id = arguments.get(user_id_param, "anonymous")
    if not isinstance(user_id, str):
        user_id = str(user_id)
    
    # Extract input
    user_input = None
    for param in [input_param, message_param, "query", "prompt", "text"]:
        if param in arguments:
            val = arguments[param]
            if isinstance(val, str):
                user_input = val
                break
            elif isinstance(val, list) and val:
                # Could be a messages list
                user_input = str(val)[:500]
                break
    
    return user_id, user_input


def _run_in_session_sync(
    func: Callable,
    agent_name: str,
    user_id_param: str,
    input_param: str,
    message_param: str,
    args: tuple,
    kwargs: dict,
) -> Any:
    """Run a function within a session context (sync)."""
    client = get_current_client()
    if not client:
        # No client configured, just run the function
        return func(*args, **kwargs)
    
    user_id, user_input = _extract_params(
        func, args, kwargs, user_id_param, input_param, message_param
    )
    
    # Create interaction
    interaction = client.begin(
        user_id=user_id,
        event=agent_name,
        input=user_input,
    )
    
    # Set context
    session_token = _session_context.set(interaction.session_id)
    client_token = _client_context.set(client)
    interaction_token = _interaction_context.set(interaction)
    
    # Also update wrappers context for backwards compatibility
    from . import wrappers
    wrappers.set_session_context(interaction.session_id, client)
    
    try:
        result = func(*args, **kwargs)
        
        # Capture output
        output = None
        if isinstance(result, str):
            output = result
        elif isinstance(result, dict) and "response" in result:
            output = str(result["response"])
        elif isinstance(result, dict) and "output" in result:
            output = str(result["output"])
        elif result is not None:
            output = str(result)[:1000]
        
        interaction.finish(output=output, success=True)
        return result
        
    except Exception as e:
        interaction.finish(
            success=False,
            failure_reason=f"{type(e).__name__}: {str(e)}",
        )
        raise
        
    finally:
        # Restore context
        _session_context.reset(session_token)
        _client_context.reset(client_token)
        _interaction_context.reset(interaction_token)
        wrappers.clear_session_context()


async def _run_in_session_async(
    func: Callable,
    agent_name: str,
    user_id_param: str,
    input_param: str,
    message_param: str,
    args: tuple,
    kwargs: dict,
) -> Any:
    """Run a function within a session context (async)."""
    client = get_current_client()
    if not client:
        return await func(*args, **kwargs)
    
    user_id, user_input = _extract_params(
        func, args, kwargs, user_id_param, input_param, message_param
    )
    
    interaction = client.begin(
        user_id=user_id,
        event=agent_name,
        input=user_input,
    )
    
    session_token = _session_context.set(interaction.session_id)
    client_token = _client_context.set(client)
    interaction_token = _interaction_context.set(interaction)
    
    from . import wrappers
    wrappers.set_session_context(interaction.session_id, client)
    
    try:
        result = await func(*args, **kwargs)
        
        output = None
        if isinstance(result, str):
            output = result
        elif isinstance(result, dict) and "response" in result:
            output = str(result["response"])
        elif isinstance(result, dict) and "output" in result:
            output = str(result["output"])
        elif result is not None:
            output = str(result)[:1000]
        
        interaction.finish(output=output, success=True)
        return result
        
    except Exception as e:
        interaction.finish(
            success=False,
            failure_reason=f"{type(e).__name__}: {str(e)}",
        )
        raise
        
    finally:
        _session_context.reset(session_token)
        _client_context.reset(client_token)
        _interaction_context.reset(interaction_token)
        wrappers.clear_session_context()


# ============================================================================
# Context Manager for Manual Session Control
# ============================================================================

class SessionContext:
    """
    Context manager for manual session control with async safety.
    
    Usage:
        async with SessionContext(user_id="123", agent="my-agent", input="Hello") as ctx:
            # All @tool calls and wrapped LLM calls are tracked
            result = await my_tool(...)
            ctx.set_output(result)
    """
    
    def __init__(
        self,
        user_id: str,
        agent: str,
        input: Optional[str] = None,
        client: Optional[SentrialClient] = None,
    ):
        self.user_id = user_id
        self.agent = agent
        self.input = input
        self._client = client or get_current_client()
        self._interaction: Optional[Interaction] = None
        self._tokens: list = []
        self._output: Optional[str] = None
    
    def __enter__(self) -> "SessionContext":
        return self._setup()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._teardown(exc_type, exc_val)
        return False
    
    async def __aenter__(self) -> "SessionContext":
        return self._setup()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._teardown(exc_type, exc_val)
        return False
    
    def _setup(self) -> "SessionContext":
        if not self._client:
            return self
        
        self._interaction = self._client.begin(
            user_id=self.user_id,
            event=self.agent,
            input=self.input,
        )
        
        self._tokens.append(_session_context.set(self._interaction.session_id))
        self._tokens.append(_client_context.set(self._client))
        self._tokens.append(_interaction_context.set(self._interaction))
        
        from . import wrappers
        wrappers.set_session_context(self._interaction.session_id, self._client)
        
        return self
    
    def _teardown(self, exc_type, exc_val):
        if self._interaction and not self._interaction._finished:
            if exc_type:
                self._interaction.finish(
                    success=False,
                    failure_reason=f"{exc_type.__name__}: {exc_val}" if exc_val else str(exc_type.__name__),
                )
            else:
                self._interaction.finish(output=self._output, success=True)
        
        # Reset context vars
        for token in reversed(self._tokens):
            try:
                if hasattr(token, 'var'):
                    token.var.reset(token)
            except Exception:
                pass
        
        from . import wrappers
        wrappers.clear_session_context()
    
    def set_output(self, output: str) -> None:
        """Set the output for this session."""
        self._output = output
    
    @property
    def session_id(self) -> Optional[str]:
        """Get the session ID."""
        return self._interaction.session_id if self._interaction else None
    
    @property
    def interaction(self) -> Optional[Interaction]:
        """Get the underlying interaction object."""
        return self._interaction
