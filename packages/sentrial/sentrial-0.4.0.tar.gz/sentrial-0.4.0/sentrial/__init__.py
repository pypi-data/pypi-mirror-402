"""
Sentrial Python SDK

Performance monitoring for AI agents. Track success rates, costs, and KPIs.

=== EASIEST: Decorators (Layer 2) ===

    from sentrial import tool, session, configure
    
    configure(api_key="sentrial_live_xxx")
    
    @tool("search")
    def search_web(query: str) -> dict:
        # Automatically tracked!
        return {"results": [...]}
    
    @session("support-agent")
    def handle_request(user_id: str, message: str):
        # Session automatically created
        # All @tool calls are tracked
        result = search_web(message)
        return result  # Captured as output

=== Auto-tracking LLM calls (Layer 1) ===

    from openai import OpenAI
    from sentrial import wrap_openai, configure, begin
    
    configure(api_key="sentrial_live_xxx")
    client = wrap_openai(OpenAI())
    
    with begin(user_id='user_123', event='chat', input=message) as interaction:
        # LLM calls are AUTOMATICALLY tracked!
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": message}]
        )
        interaction.set_output(response.choices[0].message.content)

=== FastAPI / Async Support ===

    from fastapi import FastAPI
    from openai import AsyncOpenAI
    from sentrial import wrap_openai, session, tool, configure
    
    configure(api_key="sentrial_live_xxx")
    client = wrap_openai(AsyncOpenAI())
    
    app = FastAPI()
    
    @tool("search")
    async def search_db(query: str) -> dict:
        # Async tools work too!
        return await db.search(query)
    
    @app.post("/chat")
    @session("chat-api")
    async def chat(user_id: str, message: str):
        # Session created, all LLM calls tracked
        response = await client.chat.completions.create(...)
        return {"response": response.choices[0].message.content}

=== Supported Wrappers ===

    - wrap_openai(client)     - Auto-track OpenAI/AsyncOpenAI calls
    - wrap_anthropic(client)  - Auto-track Anthropic/AsyncAnthropic calls
    - wrap_google(model)      - Auto-track Google GenerativeModel calls
    - wrap_llm(client)        - Auto-detect and wrap any supported client

=== Decorators ===

    - @tool("name")           - Track custom tool/function calls
    - @session("agent")       - Create session boundary around agent runs
    - SessionContext          - Manual session control (context manager)
"""

from .client import SentrialClient, Interaction, configure, begin
from .types import EventType
from .wrappers import (
    wrap_openai,
    wrap_anthropic,
    wrap_google,
    wrap_llm,
    set_session_context,
    clear_session_context,
    get_session_context,
)
from .decorators import (
    tool,
    session,
    SessionContext,
    get_current_session_id,
    get_current_interaction,
)

__version__ = "0.8.0"
__all__ = [
    # Core client
    "SentrialClient", 
    "Interaction", 
    "EventType", 
    "configure", 
    "begin",
    # LLM Wrappers (Layer 1)
    "wrap_openai",
    "wrap_anthropic",
    "wrap_google",
    "wrap_llm",
    "set_session_context",
    "clear_session_context",
    "get_session_context",
    # Decorators (Layer 2)
    "tool",
    "session",
    "SessionContext",
    "get_current_session_id",
    "get_current_interaction",
]

# OpenTelemetry integration (Layer 4) - only available if otel installed
try:
    from .otel import SentrialSpanProcessor, setup_otel_tracing
    __all__.extend(["SentrialSpanProcessor", "setup_otel_tracing"])
except ImportError:
    # OpenTelemetry not installed
    pass

# Async client (requires httpx)
try:
    from .async_client import (
        AsyncSentrialClient, 
        AsyncInteraction, 
        configure_async, 
        begin_async,
    )
    __all__.extend([
        "AsyncSentrialClient", 
        "AsyncInteraction", 
        "configure_async", 
        "begin_async",
    ])
except ImportError:
    # httpx not installed, async client not available
    pass

# Optional LangChain integration (only available if langchain is installed)
try:
    from .langchain import SentrialCallbackHandler
    __all__.extend(["SentrialCallbackHandler"])
except ImportError:
    # LangChain not installed, skip
    pass
