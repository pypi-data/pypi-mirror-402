# Sentrial Python SDK

**Performance monitoring and KPI tracking for AI agents.** Track success rates, costs, response times, and custom metrics across all your agent runs.

[![PyPI version](https://badge.fury.io/py/sentrial.svg)](https://badge.fury.io/py/sentrial)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎯 **KPI Tracking**: Monitor success rates, duration, costs, and custom metrics
- 📊 **Performance Analytics**: Visualize trends, compare agents, identify bottlenecks
- ✨ **AI-Powered Recommendations**: Get intelligent suggestions to improve performance
- 🔧 **Custom KPIs**: Define domain-specific metrics with LLM-as-a-Judge evaluation
- ⚡ **Zero Config**: Auto-capture agent reasoning, tool calls, and LLM interactions
- 🔌 **Framework Agnostic**: Works with LangChain, custom agents, and more
- 📈 **Visual Dashboard**: Beautiful web interface for monitoring agent performance

## Installation

### From PyPI (Recommended)

```bash
# Standard installation
pip install sentrial

# With LangChain integration
pip install sentrial[langchain]

# All integrations
pip install sentrial[all]
```

### From GitHub

```bash
pip install git+https://github.com/neelshar/Sentrial.git#subdirectory=packages/python-sdk
```

### Local Development

```bash
cd packages/python-sdk
pip install -e .
```

## Quick Start

### Basic Usage

```python
from sentrial import SentrialClient

# Initialize client (get API key from dashboard settings)
client = SentrialClient(
    api_key="sentrial_live_xxx",
    api_url="https://api.sentrial.com"  # Or your self-hosted URL
)

# Create a session for an agent run
session_id = client.create_session(
    name="Password Reset Request",
    agent_name="support-agent"  # Groups runs by agent
)

# Track tool calls
client.track_tool_call(
    session_id=session_id,
    tool_name="search_knowledge_base",
    tool_input={"query": "password reset"},
    tool_output={"articles": ["KB-001", "KB-002"]},
    reasoning="Searching for relevant articles"
)

# Track agent decisions
client.track_decision(
    session_id=session_id,
    reasoning="User already tried KB solutions. Escalating to human support.",
    alternatives=["Try another KB article", "Ask for more info", "Escalate"],
    chosen="Escalate",
    confidence=0.85
)

# Complete session
client.complete_session(
    session_id=session_id,
    status="success"
)
```

### Performance Monitoring with KPIs

Track standard and custom KPIs to measure agent effectiveness:

```python
from sentrial import SentrialClient

client = SentrialClient(
    api_key="sentrial_live_xxx",
    api_url="https://api.sentrial.com"
)

# Create session
session_id = client.create_session(
    name="Customer Support #1234",
    agent_name="support-agent",
    metadata={"user_id": "user_123", "priority": "high"}
)

# ... agent performs work ...

# Track LLM costs
input_tokens = 1500
output_tokens = 300
llm_cost = client.calculate_openai_cost("gpt-4", input_tokens, output_tokens)

# Complete session with metrics
client.complete_session(
    session_id=session_id,
    success=True,  # Did agent achieve its goal?
    estimated_cost=llm_cost,  # Total cost in USD
    custom_metrics={
        "customer_satisfaction": 95,  # Custom KPIs (0-100)
        "resolution_quality": 87,
        "response_time_seconds": 8.5,
        "issues_resolved": 3
    }
)
```

**Benefits:**
- ✅ Automatic success rate tracking across all runs
- ✅ Cost per run monitoring and trend analysis
- ✅ Custom KPI dashboards with targets
- ✅ AI-powered recommendations when KPIs underperform
- ✅ Alerts and notifications for KPI violations

### LangChain Integration

Zero-config automatic tracking for LangChain agents:

```python
from sentrial import SentrialClient, SentrialCallbackHandler
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI

# Initialize Sentrial
client = SentrialClient(api_key="sentrial_live_xxx")
session_id = client.create_session(
    name="Support Request #5678",
    agent_name="langchain-support-agent"
)

# Create callback handler
handler = SentrialCallbackHandler(client, session_id, verbose=True)

# Create your LangChain agent
llm = ChatOpenAI(model="gpt-4")
agent = create_react_agent(llm, tools, prompt)

# Add Sentrial tracking - that's it!
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    callbacks=[handler],  # ← Automatic tracking
    verbose=True
)

# Run your agent normally
result = agent_executor.invoke({
    "input": "Help user reset their password"
})

# Optionally complete with custom metrics
client.complete_session(
    session_id=session_id,
    success=True,
    custom_metrics={"customer_satisfaction": 90}
)
```

**Automatically tracked:**
- ✅ Agent reasoning (Chain of Thought)
- ✅ Tool calls (inputs, outputs, errors)
- ✅ LLM calls (prompts, responses, token usage)
- ✅ Session duration and completion status

## Configuring KPIs

Set performance targets in the dashboard:

1. Navigate to your agent in the sidebar
2. Click **"Edit KPIs"**
3. Configure standard KPIs:
   - **Success Rate**: Target % (e.g., 95%)
   - **Average Duration**: Target seconds (e.g., 10s)
   - **Cost per Run**: Target USD (e.g., $0.05)
4. Add custom KPIs with descriptions
5. Enable **LLM-as-a-Judge** for automatic evaluation

### Custom KPIs with LLM Evaluation

Define domain-specific metrics that are automatically evaluated:

```python
# In dashboard: Create custom KPI
# Name: "Customer Satisfaction"
# Target: 85
# Description: "Measures empathy, helpfulness, and issue resolution"

# In code: Just track the session
session_id = client.create_session(
    name="Support Call",
    agent_name="support-agent"
)

# ... agent does work ...

# Sentrial automatically evaluates and scores (0-100)
# based on conversation quality, empathy, resolution, etc.
client.complete_session(session_id, success=True)

# View scores, trends, and AI recommendations in dashboard
```

**Or manually provide custom metrics:**

```python
client.complete_session(
    session_id=session_id,
    success=True,
    custom_metrics={
        "customer_satisfaction": 92,  # Manually scored
        "accuracy": 88,
        "response_quality": 95
    }
)
```

## Dashboard Features

After tracking runs, view performance in the web dashboard:

- **Overview Tab**: KPI performance at a glance (green = meeting targets)
- **Analytics Tab**: Time series charts, cost trends, token usage
- **Leaderboard Tab**: Compare runs, see top performers
- **Action Items Tab**: AI recommendations to improve performance
- **Sessions View**: Drill into individual runs with full event history

## Environment Variables

Set these to avoid passing credentials in code:

```bash
# .env
SENTRIAL_API_KEY=sentrial_live_xxx
SENTRIAL_API_URL=https://api.sentrial.com  # Optional
```

```python
from sentrial import SentrialClient

# Automatically uses env vars
client = SentrialClient()
```

## Examples

See the `examples/` directory:

- **`simple_agent.py`** - Basic agent tracking
- **`langchain_agent.py`** - LangChain integration
- **`langchain_gemini.py`** - Using with Google Gemini
- **`performance_monitoring.py`** - KPI tracking and custom metrics

## API Reference

### `SentrialClient`

#### Constructor

```python
client = SentrialClient(
    api_key="...",      # Optional if SENTRIAL_API_KEY env var set
    api_url="...",      # Optional, defaults to https://api.sentrial.com
    timeout=30,         # Optional, request timeout in seconds
    max_retries=3       # Optional, max retry attempts
)
```

#### `create_session()`

Create a new agent run session:

```python
session_id = client.create_session(
    name="Support Request #123",      # Required: descriptive name
    agent_name="support-agent",       # Required: groups runs by agent
    metadata={"user_id": "user_123"}  # Optional: additional context
)
```

Returns: `str` (session ID)

#### `track_tool_call()`

Track a tool/function call:

```python
client.track_tool_call(
    session_id=session_id,
    tool_name="search_kb",
    tool_input={"query": "password reset"},
    tool_output={"articles": ["KB-001"]},
    reasoning="User needs password reset help",
    duration_ms=150  # Optional
)
```

#### `track_decision()`

Track agent reasoning and decisions:

```python
client.track_decision(
    session_id=session_id,
    reasoning="User frustrated. Need to escalate.",
    alternatives=["Try KB", "Ask questions", "Escalate"],
    chosen="Escalate",
    confidence=0.85
)
```

#### `track_llm_call()`

Track LLM API calls:

```python
client.track_llm_call(
    session_id=session_id,
    prompt="Generate support response...",
    response="Dear user, here's how...",
    model="gpt-4",
    tokens_used=250,
    cost=0.005  # Optional, in USD
)
```

#### `complete_session()`

Mark session as complete with metrics:

```python
client.complete_session(
    session_id=session_id,
    success=True,              # Required: did agent succeed?
    status="success",          # Optional: "success", "error", "cancelled"
    estimated_cost=0.05,       # Optional: total cost in USD
    custom_metrics={           # Optional: your KPIs
        "customer_satisfaction": 90,
        "resolution_quality": 85
    }
)
```

#### `calculate_openai_cost()`

Calculate OpenAI API costs:

```python
cost = client.calculate_openai_cost(
    model="gpt-4",
    input_tokens=1500,
    output_tokens=300
)
# Returns: float (cost in USD)
```

### `SentrialCallbackHandler`

LangChain callback handler for automatic tracking:

```python
handler = SentrialCallbackHandler(
    client=client,
    session_id=session_id,
    verbose=True,  # Optional: print tracking events
    track_chain_of_thought=True,  # Optional: track reasoning
    track_tool_errors=True  # Optional: track failures
)
```

## Documentation

- 📚 [Full Documentation](https://sentrial.com/docs)
- 🚀 [Quick Start Guide](https://sentrial.com/docs/quickstart)
- 🐍 [Python SDK Reference](https://sentrial.com/docs/sdk/python)
- 🔗 [LangChain Integration](https://sentrial.com/docs/integrations/langchain)

## Support

- 💬 **Discord**: [Join our community](https://discord.gg/sentrial)
- 📧 **Email**: support@sentrial.ai
- 🐛 **Issues**: [GitHub Issues](https://github.com/neelshar/Sentrial/issues)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ by the Sentrial team
