"""
Sentrial LLM Wrappers - Auto-instrument LLM provider SDKs

These wrappers automatically track all LLM calls with:
- Input messages
- Output responses  
- Token counts
- Cost estimation
- Latency

Usage:
    from openai import OpenAI
    from sentrial import wrap_openai, configure
    
    configure(api_key="sentrial_live_xxx")
    
    client = wrap_openai(OpenAI())
    
    # All calls are now automatically tracked!
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
"""

import time
import json
import contextvars
from typing import Any, Optional, TypeVar, Callable, TYPE_CHECKING
from functools import wraps

if TYPE_CHECKING:
    from openai import OpenAI, AsyncOpenAI
    from anthropic import Anthropic, AsyncAnthropic
    from google.generativeai import GenerativeModel

from .client import SentrialClient, _get_client

T = TypeVar('T')

# Context variables for async-safe session tracking
# These are isolated per async task / thread, so concurrent requests don't mix up
_current_session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'sentrial_wrapper_session_id', default=None
)
_current_client: contextvars.ContextVar[Optional[SentrialClient]] = contextvars.ContextVar(
    'sentrial_wrapper_client', default=None
)


def set_session_context(session_id: str, client: Optional[SentrialClient] = None):
    """
    Set the current session context for auto-tracking (async-safe).
    
    Call this before making LLM calls to associate them with a session.
    This is automatically called when using @session decorator or context managers.
    
    Args:
        session_id: The session ID to track LLM calls under
        client: Optional Sentrial client (uses default if not provided)
    """
    _current_session_id.set(session_id)
    if client:
        _current_client.set(client)


def clear_session_context():
    """Clear the current session context (async-safe)."""
    _current_session_id.set(None)
    _current_client.set(None)


def get_session_context() -> Optional[str]:
    """Get the current session ID (async-safe)."""
    return _current_session_id.get()


def _get_tracking_client() -> Optional[SentrialClient]:
    """Get the client to use for tracking."""
    client = _current_client.get()
    if client:
        return client
    try:
        return _get_client()
    except Exception:
        return None


# ============================================================================
# OpenAI Wrapper
# ============================================================================

def wrap_openai(client: T, track_without_session: bool = False) -> T:
    """
    Wrap an OpenAI client to automatically track all LLM calls.
    
    Args:
        client: OpenAI or AsyncOpenAI client instance
        track_without_session: If True, tracks calls even without an active session
                              (creates standalone events). Default False.
    
    Returns:
        The same client, now with auto-tracking enabled
    
    Example:
        from openai import OpenAI
        from sentrial import wrap_openai, configure
        
        configure(api_key="sentrial_live_xxx")
        client = wrap_openai(OpenAI())
        
        # Now use client normally - all calls are tracked!
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}]
        )
    """
    # Check if it's sync or async
    client_class_name = type(client).__name__
    
    if client_class_name == "OpenAI":
        _wrap_openai_sync(client, track_without_session)
    elif client_class_name == "AsyncOpenAI":
        _wrap_openai_async(client, track_without_session)
    else:
        # Try to wrap anyway - might be a subclass
        try:
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                _wrap_openai_sync(client, track_without_session)
        except Exception:
            pass
    
    return client


def _wrap_openai_sync(client: Any, track_without_session: bool = False):
    """Wrap synchronous OpenAI client methods."""
    original_create = client.chat.completions.create
    
    @wraps(original_create)
    def wrapped_create(*args, **kwargs):
        start_time = time.time()
        
        # Extract input for tracking
        messages = kwargs.get('messages', args[0] if args else [])
        model = kwargs.get('model', 'unknown')
        
        try:
            # Make the actual call
            response = original_create(*args, **kwargs)
            
            # Calculate metrics
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Extract token usage
            prompt_tokens = getattr(response.usage, 'prompt_tokens', 0) if response.usage else 0
            completion_tokens = getattr(response.usage, 'completion_tokens', 0) if response.usage else 0
            total_tokens = getattr(response.usage, 'total_tokens', 0) if response.usage else 0
            
            # Extract output
            output_content = ""
            if response.choices:
                choice = response.choices[0]
                if choice.message:
                    output_content = choice.message.content or ""
            
            # Calculate cost
            cost = SentrialClient.calculate_openai_cost(model, prompt_tokens, completion_tokens)
            
            # Track the call
            _track_llm_call(
                provider="openai",
                model=model,
                messages=messages,
                output=output_content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            _track_llm_error(
                provider="openai",
                model=model,
                messages=messages,
                error=e,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            raise
    
    client.chat.completions.create = wrapped_create


def _wrap_openai_async(client: Any, track_without_session: bool = False):
    """Wrap asynchronous OpenAI client methods."""
    original_create = client.chat.completions.create
    
    @wraps(original_create)
    async def wrapped_create(*args, **kwargs):
        start_time = time.time()
        
        messages = kwargs.get('messages', args[0] if args else [])
        model = kwargs.get('model', 'unknown')
        
        try:
            response = await original_create(*args, **kwargs)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            prompt_tokens = getattr(response.usage, 'prompt_tokens', 0) if response.usage else 0
            completion_tokens = getattr(response.usage, 'completion_tokens', 0) if response.usage else 0
            total_tokens = getattr(response.usage, 'total_tokens', 0) if response.usage else 0
            
            output_content = ""
            if response.choices:
                choice = response.choices[0]
                if choice.message:
                    output_content = choice.message.content or ""
            
            cost = SentrialClient.calculate_openai_cost(model, prompt_tokens, completion_tokens)
            
            _track_llm_call(
                provider="openai",
                model=model,
                messages=messages,
                output=output_content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            _track_llm_error(
                provider="openai",
                model=model,
                messages=messages,
                error=e,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            raise
    
    client.chat.completions.create = wrapped_create


# ============================================================================
# Anthropic Wrapper
# ============================================================================

def wrap_anthropic(client: T, track_without_session: bool = False) -> T:
    """
    Wrap an Anthropic client to automatically track all LLM calls.
    
    Args:
        client: Anthropic or AsyncAnthropic client instance
        track_without_session: If True, tracks calls even without an active session
    
    Returns:
        The same client, now with auto-tracking enabled
    
    Example:
        from anthropic import Anthropic
        from sentrial import wrap_anthropic, configure
        
        configure(api_key="sentrial_live_xxx")
        client = wrap_anthropic(Anthropic())
        
        # Now use client normally - all calls are tracked!
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    client_class_name = type(client).__name__
    
    if client_class_name == "Anthropic":
        _wrap_anthropic_sync(client, track_without_session)
    elif client_class_name == "AsyncAnthropic":
        _wrap_anthropic_async(client, track_without_session)
    else:
        try:
            if hasattr(client, 'messages') and hasattr(client.messages, 'create'):
                _wrap_anthropic_sync(client, track_without_session)
        except Exception:
            pass
    
    return client


def _wrap_anthropic_sync(client: Any, track_without_session: bool = False):
    """Wrap synchronous Anthropic client methods."""
    original_create = client.messages.create
    
    @wraps(original_create)
    def wrapped_create(*args, **kwargs):
        start_time = time.time()
        
        messages = kwargs.get('messages', [])
        model = kwargs.get('model', 'unknown')
        system = kwargs.get('system', '')
        
        try:
            response = original_create(*args, **kwargs)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Anthropic usage
            prompt_tokens = getattr(response.usage, 'input_tokens', 0) if response.usage else 0
            completion_tokens = getattr(response.usage, 'output_tokens', 0) if response.usage else 0
            total_tokens = prompt_tokens + completion_tokens
            
            # Extract output
            output_content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        output_content += block.text
            
            cost = SentrialClient.calculate_anthropic_cost(model, prompt_tokens, completion_tokens)
            
            # Include system prompt in messages for tracking
            full_messages = messages
            if system:
                full_messages = [{"role": "system", "content": system}] + list(messages)
            
            _track_llm_call(
                provider="anthropic",
                model=model,
                messages=full_messages,
                output=output_content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            _track_llm_error(
                provider="anthropic",
                model=model,
                messages=messages,
                error=e,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            raise
    
    client.messages.create = wrapped_create


def _wrap_anthropic_async(client: Any, track_without_session: bool = False):
    """Wrap asynchronous Anthropic client methods."""
    original_create = client.messages.create
    
    @wraps(original_create)
    async def wrapped_create(*args, **kwargs):
        start_time = time.time()
        
        messages = kwargs.get('messages', [])
        model = kwargs.get('model', 'unknown')
        system = kwargs.get('system', '')
        
        try:
            response = await original_create(*args, **kwargs)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            prompt_tokens = getattr(response.usage, 'input_tokens', 0) if response.usage else 0
            completion_tokens = getattr(response.usage, 'output_tokens', 0) if response.usage else 0
            total_tokens = prompt_tokens + completion_tokens
            
            output_content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        output_content += block.text
            
            cost = SentrialClient.calculate_anthropic_cost(model, prompt_tokens, completion_tokens)
            
            full_messages = messages
            if system:
                full_messages = [{"role": "system", "content": system}] + list(messages)
            
            _track_llm_call(
                provider="anthropic",
                model=model,
                messages=full_messages,
                output=output_content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            _track_llm_error(
                provider="anthropic",
                model=model,
                messages=messages,
                error=e,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            raise
    
    client.messages.create = wrapped_create


# ============================================================================
# Google/Gemini Wrapper
# ============================================================================

def wrap_google(client: T, track_without_session: bool = False) -> T:
    """
    Wrap a Google GenerativeModel to automatically track all LLM calls.
    
    Args:
        client: google.generativeai.GenerativeModel instance
        track_without_session: If True, tracks calls even without an active session
    
    Returns:
        The same client, now with auto-tracking enabled
    
    Example:
        import google.generativeai as genai
        from sentrial import wrap_google, configure
        
        configure(api_key="sentrial_live_xxx")
        
        genai.configure(api_key="your-google-key")
        model = wrap_google(genai.GenerativeModel("gemini-2.0-flash"))
        
        # Now use model normally - all calls are tracked!
        response = model.generate_content("Hello!")
    """
    _wrap_google_model(client, track_without_session)
    return client


def _wrap_google_model(model: Any, track_without_session: bool = False):
    """Wrap Google GenerativeModel methods."""
    original_generate = model.generate_content
    
    @wraps(original_generate)
    def wrapped_generate(contents, *args, **kwargs):
        start_time = time.time()
        
        # Extract model name
        model_name = getattr(model, 'model_name', 'gemini-unknown')
        if model_name.startswith('models/'):
            model_name = model_name[7:]  # Remove 'models/' prefix
        
        # Convert contents to messages format for tracking
        messages = _google_contents_to_messages(contents)
        
        try:
            response = original_generate(contents, *args, **kwargs)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Extract usage metadata
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                completion_tokens = getattr(usage, 'candidates_token_count', 0)
            total_tokens = prompt_tokens + completion_tokens
            
            # Extract output
            output_content = ""
            if response.text:
                output_content = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                output_content += part.text
            
            cost = SentrialClient.calculate_google_cost(model_name, prompt_tokens, completion_tokens)
            
            _track_llm_call(
                provider="google",
                model=model_name,
                messages=messages,
                output=output_content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            _track_llm_error(
                provider="google",
                model=model_name,
                messages=messages,
                error=e,
                duration_ms=duration_ms,
                track_without_session=track_without_session,
            )
            raise
    
    model.generate_content = wrapped_generate
    
    # Also wrap async if available
    if hasattr(model, 'generate_content_async'):
        original_async = model.generate_content_async
        
        @wraps(original_async)
        async def wrapped_async(contents, *args, **kwargs):
            start_time = time.time()
            model_name = getattr(model, 'model_name', 'gemini-unknown')
            if model_name.startswith('models/'):
                model_name = model_name[7:]
            
            messages = _google_contents_to_messages(contents)
            
            try:
                response = await original_async(contents, *args, **kwargs)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                prompt_tokens = 0
                completion_tokens = 0
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                    completion_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = prompt_tokens + completion_tokens
                
                output_content = ""
                if response.text:
                    output_content = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    output_content += part.text
                
                cost = SentrialClient.calculate_google_cost(model_name, prompt_tokens, completion_tokens)
                
                _track_llm_call(
                    provider="google",
                    model=model_name,
                    messages=messages,
                    output=output_content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost=cost,
                    duration_ms=duration_ms,
                    track_without_session=track_without_session,
                )
                
                return response
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                _track_llm_error(
                    provider="google",
                    model=model_name,
                    messages=messages,
                    error=e,
                    duration_ms=duration_ms,
                    track_without_session=track_without_session,
                )
                raise
        
        model.generate_content_async = wrapped_async


def _google_contents_to_messages(contents: Any) -> list:
    """Convert Google's contents format to standard messages format."""
    if isinstance(contents, str):
        return [{"role": "user", "content": contents}]
    elif isinstance(contents, list):
        messages = []
        for item in contents:
            if isinstance(item, str):
                messages.append({"role": "user", "content": item})
            elif hasattr(item, 'role') and hasattr(item, 'parts'):
                # Google Content object
                content = ""
                for part in item.parts:
                    if hasattr(part, 'text'):
                        content += part.text
                messages.append({"role": item.role, "content": content})
            elif isinstance(item, dict):
                messages.append(item)
        return messages
    else:
        return [{"role": "user", "content": str(contents)}]


# ============================================================================
# Common Tracking Functions
# ============================================================================

def _track_llm_call(
    provider: str,
    model: str,
    messages: list,
    output: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost: float,
    duration_ms: int,
    track_without_session: bool = False,
):
    """Track an LLM call to Sentrial."""
    client = _get_tracking_client()
    if not client:
        return
    
    session_id = _current_session_id.get()
    
    if not session_id and not track_without_session:
        # No active session and we're not tracking standalone
        return
    
    # Format input for tracking
    try:
        input_data = {
            "messages": messages,
            "model": model,
            "provider": provider,
        }
    except Exception:
        input_data = {"raw": str(messages)}
    
    output_data = {
        "content": output,
        "tokens": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": total_tokens,
        },
        "cost_usd": cost,
    }
    
    if session_id:
        # Track as a tool call under the session
        try:
            client.track_tool_call(
                session_id=session_id,
                tool_name=f"llm:{provider}:{model}",
                tool_input=input_data,
                tool_output=output_data,
                reasoning=f"LLM call to {provider} {model}",
                estimated_cost=cost,
                token_count=total_tokens,
                metadata={
                    "provider": provider,
                    "model": model,
                    "duration_ms": duration_ms,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                },
            )
        except Exception as e:
            # Don't let tracking errors break the user's code
            import logging
            logging.warning(f"Sentrial: Failed to track LLM call: {e}")


def _track_llm_error(
    provider: str,
    model: str,
    messages: list,
    error: Exception,
    duration_ms: int,
    track_without_session: bool = False,
):
    """Track an LLM error to Sentrial."""
    client = _get_tracking_client()
    if not client:
        return
    
    session_id = _current_session_id.get()
    
    if not session_id and not track_without_session:
        return
    
    if session_id:
        try:
            client.track_error(
                session_id=session_id,
                error_message=str(error),
                error_type=type(error).__name__,
                tool_name=f"llm:{provider}:{model}",
                metadata={
                    "provider": provider,
                    "model": model,
                    "duration_ms": duration_ms,
                },
            )
        except Exception as e:
            import logging
            logging.warning(f"Sentrial: Failed to track LLM error: {e}")


# ============================================================================
# Convenience Functions
# ============================================================================

def wrap_llm(client: T, provider: Optional[str] = None) -> T:
    """
    Auto-detect and wrap any supported LLM client.
    
    Args:
        client: Any supported LLM client (OpenAI, Anthropic, Google)
        provider: Optional provider hint ("openai", "anthropic", "google")
    
    Returns:
        The wrapped client
    
    Example:
        from openai import OpenAI
        from sentrial import wrap_llm
        
        client = wrap_llm(OpenAI())  # Auto-detected as OpenAI
    """
    client_class = type(client).__name__
    client_module = type(client).__module__
    
    # Try to auto-detect
    if provider == "openai" or "openai" in client_module.lower() or client_class in ("OpenAI", "AsyncOpenAI"):
        return wrap_openai(client)
    elif provider == "anthropic" or "anthropic" in client_module.lower() or client_class in ("Anthropic", "AsyncAnthropic"):
        return wrap_anthropic(client)
    elif provider == "google" or "google" in client_module.lower() or "GenerativeModel" in client_class:
        return wrap_google(client)
    else:
        import logging
        logging.warning(f"Sentrial: Unknown LLM client type: {client_class}. No auto-tracking applied.")
        return client
