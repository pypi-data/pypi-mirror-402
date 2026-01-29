# Sentrial Python SDK

**The easiest way to add observability to your AI agents.** One line of code to track LLM calls, tool executions, costs, and latency.

[![PyPI version](https://img.shields.io/badge/pypi%20package-0.4.2-brightgreen)](https://pypi.org/project/sentrial/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why Sentrial?

| Feature | Sentrial | Others |
|---------|----------|--------|
| **Setup time** | 1 line | Hours of config |
| **Auto-tracking** | ✔️ LLM calls, tools, costs | Manual instrumentation |
| **Framework support** | OpenAI, Anthropic, Google, LangChain, OpenTelemetry | Limited |
| **Async-safe** | ✔️ Built for FastAPI/async | Often breaks |

## Installation

```bash
# Core (works with any framework)
pip install sentrial

# With specific providers
pip install sentrial[openai]      # OpenAI auto-tracking
pip install sentrial[anthropic]   # Anthropic auto-tracking
pip install sentrial[google]      # Google/Gemini auto-tracking
pip install sentrial[langchain]   # LangChain callback handler
pip install sentrial[otel]        # OpenTelemetry integration

# Everything
pip install sentrial[all]
```

## Quick Start (30 seconds)

### Option 1: Wrap your LLM client (Recommended)

**OpenAI:**
```python
from sentrial import wrap_openai, configure, begin
from openai import OpenAI

configure(api_key="sentrial_live_xxx")
client = wrap_openai(OpenAI())  # ← That's it!

with begin(user_id="user_123", event="chat", input=user_message) as session:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_message}]
    )
    # ✔️ Automatically tracked: model, tokens, cost, latency
    session.set_output(response.choices[0].message.content)
```

**Anthropic:**
```python
from sentrial import wrap_anthropic, configure, begin
from anthropic import Anthropic

configure(api_key="sentrial_live_xxx")
client = wrap_anthropic(Anthropic())

with begin(user_id="user_123", event="chat", input=user_message) as session:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}]
    )
    session.set_output(response.content[0].text)
```

**Google Gemini:**
```python
from sentrial import wrap_google, configure, begin
import google.generativeai as genai

configure(api_key="sentrial_live_xxx")
genai.configure(api_key="your_google_key")
model = wrap_google(genai.GenerativeModel("gemini-2.5-pro"))

with begin(user_id="user_123", event="chat", input=prompt) as session:
    response = model.generate_content(prompt)
    session.set_output(response.text)
```

### Option 2: Use decorators (Simplest)

```python
from sentrial import tool, session, configure

configure(api_key="sentrial_live_xxx")

@tool("search_web")
def search_web(query: str) -> dict:
    """Tool calls are automatically tracked"""
    return {"results": [...]}

@tool("get_weather")
def get_weather(city: str) -> dict:
    return {"temp": 72, "condition": "sunny"}

@session("my-agent")
def run_agent(user_id: str, message: str) -> str:
    """Session boundary - tracks input/output automatically"""
    results = search_web(message)
    weather = get_weather("San Francisco")
    return f"Found {len(results)} results. Weather: {weather}"

# Run it - everything is tracked!
run_agent(user_id="user_123", message="What's happening today?")
```

### Option 3: FastAPI / Async

```python
from fastapi import FastAPI
from sentrial import AsyncSentrialClient
from contextlib import asynccontextmanager

sentrial = AsyncSentrialClient(
    api_key="sentrial_live_xxx",
    api_url="http://localhost:3001"
)

@asynccontextmanager
async def lifespan(app):
    yield
    await sentrial.close()

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(request: ChatRequest):
    async with await sentrial.begin(
        user_id=request.user_id,
        event="chat",
        input=request.message,
    ) as session:
        # Your agent logic here
        result = await call_llm(request.message)
        
        await session.track_tool_call(
            tool_name="llm_call",
            tool_input={"prompt": request.message},
            tool_output={"response": result}
        )
        
        session.set_output(result)
        return {"response": result}
```

### Option 4: LangChain

```python
from sentrial import SentrialClient
from sentrial.langchain import SentrialCallbackHandler
from langchain.agents import AgentExecutor, create_react_agent

client = SentrialClient(api_key="sentrial_live_xxx")

session_id = client.create_session(
    name="Support Request",
    agent_name="support-agent",
    user_id="user_123"
)

handler = SentrialCallbackHandler(client=client, session_id=session_id)
handler.set_input(user_query)

result = agent_executor.invoke(
    {"input": user_query},
    {"callbacks": [handler]}
)

handler.finish(success=True)
```

### Option 5: OpenTelemetry (Enterprise)

Works with any OTel-instrumented framework (Vercel AI SDK, LangChain, etc.):

```python
from sentrial.otel import setup_otel_tracing

# One line setup
setup_otel_tracing(
    api_key="sentrial_live_xxx",
    project="my-ai-app"
)

# Now ANY OTel-instrumented library sends traces to Sentrial!
# Works with: opentelemetry-instrumentation-openai, traceloop, etc.
```

Or add to existing OTel setup:

```python
from opentelemetry.sdk.trace import TracerProvider
from sentrial.otel import SentrialSpanProcessor

provider = TracerProvider()
provider.add_span_processor(SentrialSpanProcessor(
    api_key="sentrial_live_xxx",
    project="my-ai-app"
))
```

## What Gets Tracked

| Data | Auto-tracked | Manual |
|------|-------------|--------|
| LLM calls (prompt, response) | ✔️ via wrappers | `track_decision()` |
| Token usage | ✔️ via wrappers | `tokens_used` param |
| Cost (USD) | ✔️ calculated | `estimated_cost` param |
| Latency | ✔️ always | - |
| Tool calls | ✔️ via `@tool` | `track_tool_call()` |
| Errors | ✔️ always | `track_error()` |
| User ID | ✔️ via session | `user_id` param |
| Custom metrics | - | `custom_metrics` param |

## Environment Variables

```bash
export SENTRIAL_API_KEY=sentrial_live_xxx
export SENTRIAL_API_URL=https://api.sentrial.com  # or http://localhost:3001 for local
```

Then just:
```python
from sentrial import configure
configure()  # Uses env vars automatically
```

## API Reference

### Configuration

```python
from sentrial import configure

configure(
    api_key="sentrial_live_xxx",      # Or SENTRIAL_API_KEY env var
    api_url="https://api.sentrial.com" # Or SENTRIAL_API_URL env var
)
```

### LLM Wrappers

```python
from sentrial import wrap_openai, wrap_anthropic, wrap_google

# Wrap once, use everywhere
openai_client = wrap_openai(OpenAI())
anthropic_client = wrap_anthropic(Anthropic())
google_model = wrap_google(genai.GenerativeModel("gemini-2.5-pro"))
```

### Context Manager

```python
from sentrial import begin

with begin(
    user_id="user_123",           # Required: for user analytics
    event="agent_name",           # Required: groups sessions
    input="user message",         # Optional: captured as session input
) as session:
    # Track tool calls
    session.track_tool_call(
        tool_name="search",
        tool_input={"query": "..."},
        tool_output={"results": [...]}
    )
    
    # Track decisions/reasoning
    session.track_decision(
        reasoning="Choosing to search because...",
        confidence=0.9
    )
    
    # Set output
    session.set_output("Final response to user")
```

### Decorators

```python
from sentrial import tool, session

@tool("tool_name")
def my_tool(arg1: str) -> dict:
    """Automatically tracked when called within a session"""
    return {"result": "..."}

@session("agent_name")
def my_agent(user_id: str, message: str) -> str:
    """Creates session, tracks input/output, handles errors"""
    return my_tool(message)
```

### Async Client

```python
from sentrial import AsyncSentrialClient

client = AsyncSentrialClient(api_key="...")

async with await client.begin(user_id="...", event="...") as session:
    await session.track_tool_call(...)
    session.set_output("...")

# Don't forget to close when done
await client.close()
```

## Framework Compatibility

| Framework | Integration | Status |
|-----------|-------------|--------|
| **Direct OpenAI** | `wrap_openai()` | ✔️ |
| **Direct Anthropic** | `wrap_anthropic()` | ✔️ |
| **Direct Gemini** | `wrap_google()` | ✔️ |
| **FastAPI** | `AsyncSentrialClient` | ✔️ |
| **LangChain** | `SentrialCallbackHandler` | ✔️ |
| **LlamaIndex** | OpenTelemetry | ✔️ |
| **CrewAI** | OpenTelemetry | ✔️ |
| **Vercel AI SDK** | OpenTelemetry | ✔️ |
| **Custom agents** | Decorators or manual | ✔️ |

## Examples

See the [`examples/`](https://github.com/neelshar/Sentrial/tree/main/examples) directory:

- `openai_wrapper_example.py` - OpenAI auto-tracking
- `anthropic_wrapper_example.py` - Anthropic auto-tracking  
- `google_wrapper_example.py` - Gemini auto-tracking
- `decorator_example.py` - Using `@tool` and `@session`
- `fastapi_agent.py` - Full FastAPI integration
- `otel_example.py` - OpenTelemetry setup
- `langchain_agent.py` - LangChain callback handler

## Dashboard Features

After tracking, view in the web dashboard:

- **Sessions**: See all agent runs with input/output
- **Events**: Drill into tool calls, LLM decisions, errors
- **Users**: Track daily active users, session counts
- **Agents**: Compare performance across agents
- **Analytics**: Cost trends, latency percentiles, token usage

## Support

- 📚 [Documentation](https://www.sentrial.com/docs)
- 💬 [Discord](https://discord.gg/9bMmJCXt)
- 📧 [Email](mailto:neel@sentrial.com)
- 🐛 [GitHub Issues](https://github.com/neelshar/Sentrial/issues)

## License

MIT License - see [LICENSE](LICENSE) for details.
