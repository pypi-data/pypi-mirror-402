"""
Sentrial OpenTelemetry Integration

Provides a SpanProcessor that sends OTel traces to Sentrial.
This enables automatic compatibility with:
- Vercel AI SDK
- LangChain (with OTel instrumentation)
- OpenLLMetry instrumented libraries
- Any framework emitting OTel GenAI traces

Usage:
    from opentelemetry.sdk.trace import TracerProvider
    from sentrial.otel import SentrialSpanProcessor
    
    provider = TracerProvider()
    provider.add_span_processor(SentrialSpanProcessor(
        api_key="sentrial_live_xxx",
        project="my-project"
    ))

With existing OTel setup (Sentry, Datadog, etc.):
    from opentelemetry.sdk.trace import TracerProvider
    from sentrial.otel import SentrialSpanProcessor
    
    provider = TracerProvider()
    provider.add_span_processor(your_existing_processor)
    provider.add_span_processor(SentrialSpanProcessor())  # Add Sentrial alongside
"""

import json
import os
import logging
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry - gracefully handle if not installed
try:
    from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
    from opentelemetry.trace import SpanKind, StatusCode
    from opentelemetry.context import Context
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    SpanProcessor = object  # Fallback for type hints
    ReadableSpan = object

from .client import SentrialClient


class SentrialSpanProcessor(SpanProcessor if OTEL_AVAILABLE else object):
    """
    OpenTelemetry SpanProcessor that sends traces to Sentrial.
    
    Automatically converts OTel GenAI spans to Sentrial events, capturing:
    - LLM calls (input messages, output, tokens, cost)
    - Tool executions
    - Agent decisions
    
    Args:
        api_key: Sentrial API key (defaults to SENTRIAL_API_KEY env var)
        api_url: Sentrial API URL (defaults to SENTRIAL_API_URL env var)
        project: Project name for grouping traces (defaults to SENTRIAL_PROJECT env var)
        filter_ai_spans: If True, only send AI-related spans (default: True)
        custom_filter: Optional function to filter spans (span) -> bool
        user_id_attribute: Attribute name containing user ID (default: "user.id")
        
    Usage:
        from opentelemetry.sdk.trace import TracerProvider
        from sentrial.otel import SentrialSpanProcessor
        
        provider = TracerProvider()
        provider.add_span_processor(SentrialSpanProcessor(
            project="my-ai-project"
        ))
        trace.set_tracer_provider(provider)
        
        # Now any OTel-instrumented LLM library sends traces to Sentrial!
    """
    
    # GenAI semantic conventions prefixes
    GENAI_PREFIXES = ("gen_ai.", "llm.", "ai.", "openai.", "anthropic.", "cohere.")
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        project: Optional[str] = None,
        filter_ai_spans: bool = True,
        custom_filter: Optional[Callable[[Any], Optional[bool]]] = None,
        user_id_attribute: str = "user.id",
    ):
        if not OTEL_AVAILABLE:
            raise ImportError(
                "OpenTelemetry is not installed. "
                "Install it with: pip install opentelemetry-api opentelemetry-sdk"
            )
        
        self.api_key = api_key or os.environ.get("SENTRIAL_API_KEY")
        self.api_url = api_url or os.environ.get("SENTRIAL_API_URL", "https://api.sentrial.com")
        self.project = project or os.environ.get("SENTRIAL_PROJECT", "otel-traces")
        self.filter_ai_spans = filter_ai_spans
        self.custom_filter = custom_filter
        self.user_id_attribute = user_id_attribute
        
        self._client = SentrialClient(api_key=self.api_key, api_url=self.api_url)
        
        # Track active sessions by trace_id
        self._sessions: Dict[str, str] = {}  # trace_id -> session_id
    
    def on_start(self, span: "ReadableSpan", parent_context: Optional["Context"] = None) -> None:
        """Called when a span starts. We don't need to do anything here."""
        pass
    
    def on_end(self, span: "ReadableSpan") -> None:
        """
        Called when a span ends. Process and send to Sentrial.
        """
        try:
            # Apply filters
            if not self._should_process_span(span):
                return
            
            # Extract span data
            span_data = self._extract_span_data(span)
            
            # Get or create session for this trace
            trace_id = format(span.context.trace_id, '032x')
            session_id = self._get_or_create_session(trace_id, span_data)
            
            # Determine event type and track
            if self._is_llm_span(span_data):
                self._track_llm_event(session_id, span_data)
            elif self._is_tool_span(span_data):
                self._track_tool_event(session_id, span_data)
            else:
                self._track_generic_event(session_id, span_data)
                
        except Exception as e:
            logger.warning(f"Sentrial: Failed to process span: {e}")
    
    def shutdown(self) -> None:
        """Clean up resources."""
        # Complete any open sessions
        for trace_id, session_id in list(self._sessions.items()):
            try:
                self._client.complete_session(session_id, success=True)
            except Exception:
                pass
        self._sessions.clear()
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any pending data."""
        return True
    
    def _should_process_span(self, span: "ReadableSpan") -> bool:
        """Determine if this span should be processed."""
        # Apply custom filter first
        if self.custom_filter:
            result = self.custom_filter(span)
            if result is not None:
                return result
        
        # If filtering AI spans only
        if self.filter_ai_spans:
            return self._is_ai_span(span)
        
        return True
    
    def _is_ai_span(self, span: "ReadableSpan") -> bool:
        """Check if this is an AI/LLM related span."""
        name = span.name.lower()
        
        # Check span name
        if any(prefix in name for prefix in ("llm", "chat", "completion", "generate", "embed")):
            return True
        
        # Check attributes
        attributes = dict(span.attributes or {})
        for key in attributes.keys():
            if any(key.startswith(prefix) for prefix in self.GENAI_PREFIXES):
                return True
        
        return False
    
    def _extract_span_data(self, span: "ReadableSpan") -> Dict[str, Any]:
        """Extract relevant data from an OTel span."""
        attributes = dict(span.attributes or {})
        
        # Basic span info
        data = {
            "name": span.name,
            "trace_id": format(span.context.trace_id, '032x'),
            "span_id": format(span.context.span_id, '016x'),
            "parent_span_id": format(span.parent.span_id, '016x') if span.parent else None,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "duration_ns": (span.end_time - span.start_time) if span.end_time and span.start_time else 0,
            "duration_ms": int((span.end_time - span.start_time) / 1_000_000) if span.end_time and span.start_time else 0,
            "status": span.status.status_code.name if span.status else "UNSET",
            "kind": span.kind.name if span.kind else "INTERNAL",
            "attributes": attributes,
        }
        
        # Extract GenAI specific attributes
        data.update(self._extract_genai_attributes(attributes))
        
        # Extract user ID
        data["user_id"] = attributes.get(self.user_id_attribute, "anonymous")
        
        return data
    
    def _extract_genai_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Extract GenAI semantic convention attributes."""
        result = {
            "model": None,
            "provider": None,
            "input_messages": None,
            "output_messages": None,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "operation": None,
            "tool_name": None,
            "tool_input": None,
            "tool_output": None,
        }
        
        # Model and provider
        for key in ["gen_ai.request.model", "llm.model", "ai.model", "model"]:
            if key in attributes:
                model = str(attributes[key])
                # Strip provider prefix (e.g., "openai/gpt-4o" -> "gpt-4o")
                for prefix in ["openai/", "anthropic/", "google/", "cohere/"]:
                    if model.startswith(prefix):
                        model = model[len(prefix):]
                result["model"] = model
                break
        
        # Provider
        for key in ["gen_ai.system", "llm.provider", "ai.provider"]:
            if key in attributes:
                result["provider"] = str(attributes[key])
                break
        
        # Input messages
        for key in ["gen_ai.prompt", "gen_ai.prompt_json", "gen_ai.input.messages", "llm.input"]:
            if key in attributes:
                val = attributes[key]
                if isinstance(val, str):
                    try:
                        result["input_messages"] = json.loads(val)
                    except json.JSONDecodeError:
                        result["input_messages"] = [{"role": "user", "content": val}]
                else:
                    result["input_messages"] = val
                break
        
        # Output messages
        for key in ["gen_ai.completion", "gen_ai.completion_json", "gen_ai.output.messages", "llm.output"]:
            if key in attributes:
                val = attributes[key]
                if isinstance(val, str):
                    try:
                        result["output_messages"] = json.loads(val)
                    except json.JSONDecodeError:
                        result["output_messages"] = [{"role": "assistant", "content": val}]
                else:
                    result["output_messages"] = val
                break
        
        # Token usage
        for key in ["gen_ai.usage.prompt_tokens", "gen_ai.usage.input_tokens", "llm.token_count.prompt"]:
            if key in attributes:
                result["prompt_tokens"] = int(attributes[key])
                break
        
        for key in ["gen_ai.usage.completion_tokens", "gen_ai.usage.output_tokens", "llm.token_count.completion"]:
            if key in attributes:
                result["completion_tokens"] = int(attributes[key])
                break
        
        for key in ["gen_ai.usage.total_tokens", "llm.token_count.total"]:
            if key in attributes:
                result["total_tokens"] = int(attributes[key])
                break
        
        if result["total_tokens"] == 0 and (result["prompt_tokens"] or result["completion_tokens"]):
            result["total_tokens"] = result["prompt_tokens"] + result["completion_tokens"]
        
        # Operation type
        for key in ["gen_ai.operation.name", "llm.operation"]:
            if key in attributes:
                result["operation"] = str(attributes[key])
                break
        
        # Tool info
        for key in ["gen_ai.tool.name", "tool.name"]:
            if key in attributes:
                result["tool_name"] = str(attributes[key])
                break
        
        return result
    
    def _is_llm_span(self, span_data: Dict[str, Any]) -> bool:
        """Check if this span represents an LLM call."""
        if span_data.get("model"):
            return True
        
        operation = span_data.get("operation", "").lower()
        if operation in ("chat", "completion", "generate", "embed"):
            return True
        
        name = span_data.get("name", "").lower()
        if any(x in name for x in ("chat.completion", "generate", "llm")):
            return True
        
        return False
    
    def _is_tool_span(self, span_data: Dict[str, Any]) -> bool:
        """Check if this span represents a tool execution."""
        if span_data.get("tool_name"):
            return True
        
        operation = span_data.get("operation", "").lower()
        if operation in ("execute_tool", "tool"):
            return True
        
        name = span_data.get("name", "").lower()
        if "tool" in name:
            return True
        
        return False
    
    def _get_or_create_session(self, trace_id: str, span_data: Dict[str, Any]) -> str:
        """Get existing session for trace or create new one."""
        if trace_id in self._sessions:
            return self._sessions[trace_id]
        
        # Create new session
        user_id = span_data.get("user_id", "anonymous")
        
        session_id = self._client.create_session(
            name=f"OTel Trace: {trace_id[:8]}",
            agent_name=self.project,
            user_id=user_id,
            metadata={
                "trace_id": trace_id,
                "source": "opentelemetry",
            },
        )
        
        self._sessions[trace_id] = session_id
        return session_id
    
    def _track_llm_event(self, session_id: str, span_data: Dict[str, Any]) -> None:
        """Track an LLM call event."""
        model = span_data.get("model", "unknown")
        provider = span_data.get("provider", "unknown")
        
        input_data = {
            "messages": span_data.get("input_messages"),
            "model": model,
            "provider": provider,
        }
        
        output_data = {
            "messages": span_data.get("output_messages"),
            "tokens": {
                "prompt": span_data.get("prompt_tokens", 0),
                "completion": span_data.get("completion_tokens", 0),
                "total": span_data.get("total_tokens", 0),
            },
        }
        
        # Calculate cost
        prompt_tokens = span_data.get("prompt_tokens", 0)
        completion_tokens = span_data.get("completion_tokens", 0)
        cost = self._calculate_cost(provider, model, prompt_tokens, completion_tokens)
        
        self._client.track_tool_call(
            session_id=session_id,
            tool_name=f"llm:{provider}:{model}",
            tool_input=input_data,
            tool_output=output_data,
            reasoning=f"LLM call via OpenTelemetry",
            estimated_cost=cost,
            token_count=span_data.get("total_tokens", 0),
            trace_id=span_data.get("trace_id"),
            span_id=span_data.get("span_id"),
            metadata={
                "duration_ms": span_data.get("duration_ms", 0),
                "otel_span_name": span_data.get("name"),
            },
        )
    
    def _track_tool_event(self, session_id: str, span_data: Dict[str, Any]) -> None:
        """Track a tool execution event."""
        tool_name = span_data.get("tool_name") or span_data.get("name", "unknown_tool")
        
        self._client.track_tool_call(
            session_id=session_id,
            tool_name=tool_name,
            tool_input=span_data.get("tool_input") or {"otel_attributes": span_data.get("attributes", {})},
            tool_output=span_data.get("tool_output") or {"status": span_data.get("status", "UNSET")},
            trace_id=span_data.get("trace_id"),
            span_id=span_data.get("span_id"),
            metadata={
                "duration_ms": span_data.get("duration_ms", 0),
                "otel_span_name": span_data.get("name"),
            },
        )
    
    def _track_generic_event(self, session_id: str, span_data: Dict[str, Any]) -> None:
        """Track a generic span as a decision/step."""
        self._client.track_decision(
            session_id=session_id,
            reasoning=f"OTel span: {span_data.get('name')}",
            trace_id=span_data.get("trace_id"),
            span_id=span_data.get("span_id"),
            metadata={
                "duration_ms": span_data.get("duration_ms", 0),
                "otel_attributes": span_data.get("attributes", {}),
            },
        )
    
    def _calculate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost based on provider and model."""
        if not prompt_tokens and not completion_tokens:
            return 0.0
        
        provider_lower = (provider or "").lower()
        
        if "openai" in provider_lower or model.startswith("gpt"):
            return SentrialClient.calculate_openai_cost(model, prompt_tokens, completion_tokens)
        elif "anthropic" in provider_lower or model.startswith("claude"):
            return SentrialClient.calculate_anthropic_cost(model, prompt_tokens, completion_tokens)
        elif "google" in provider_lower or model.startswith("gemini"):
            return SentrialClient.calculate_google_cost(model, prompt_tokens, completion_tokens)
        
        # Default: assume GPT-4 pricing
        return SentrialClient.calculate_openai_cost("gpt-4", prompt_tokens, completion_tokens)


# Convenience function for quick setup
def setup_otel_tracing(
    project: Optional[str] = None,
    api_key: Optional[str] = None,
    filter_ai_spans: bool = True,
) -> None:
    """
    Quick setup for OpenTelemetry tracing to Sentrial.
    
    This sets up a basic TracerProvider with Sentrial as the processor.
    For more control, create the SentrialSpanProcessor directly.
    
    Args:
        project: Project name for grouping traces
        api_key: Sentrial API key (defaults to SENTRIAL_API_KEY env var)
        filter_ai_spans: Only send AI-related spans (default: True)
    
    Usage:
        from sentrial.otel import setup_otel_tracing
        
        setup_otel_tracing(project="my-ai-app")
        
        # Now any OTel-instrumented code sends traces to Sentrial!
    """
    if not OTEL_AVAILABLE:
        raise ImportError(
            "OpenTelemetry is not installed. "
            "Install it with: pip install opentelemetry-api opentelemetry-sdk"
        )
    
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    
    provider = TracerProvider()
    provider.add_span_processor(SentrialSpanProcessor(
        project=project,
        api_key=api_key,
        filter_ai_spans=filter_ai_spans,
    ))
    trace.set_tracer_provider(provider)
