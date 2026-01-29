"""Sentrial Async Client - Async SDK interface for FastAPI and other async frameworks"""

import os
from typing import Any, Optional, Dict

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .types import EventType


class AsyncSentrialClient:
    """
    Async Sentrial Client for tracking agent performance and KPIs.
    
    Designed for use with FastAPI, asyncio, and other async Python frameworks.

    Usage:
        client = AsyncSentrialClient(
            api_key="sentrial_live_xxx",
            api_url="https://api.sentrial.com"
        )

        # Create a session for an agent run
        session_id = await client.create_session(
            name="Support Request #123",
            agent_name="support-agent",
            user_id="user_456"
        )

        # Track events
        await client.track_tool_call(
            session_id=session_id,
            tool_name="search_kb",
            tool_input={"query": "password reset"},
            tool_output={"articles": ["KB-001"]}
        )

        # Complete session with metrics
        await client.complete_session(
            session_id=session_id,
            success=True,
            custom_metrics={"customer_satisfaction": 90}
        )
        
        # Don't forget to close!
        await client.close()
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize async Sentrial client.

        Args:
            api_url: URL of the Sentrial API server (defaults to SENTRIAL_API_URL env var or production)
            api_key: API key for authentication (defaults to SENTRIAL_API_KEY env var)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for AsyncSentrialClient. "
                "Install with: pip install httpx"
            )
        
        self.api_url = (api_url or os.environ.get("SENTRIAL_API_URL", "https://api.sentrial.com")).rstrip("/")
        self.api_key = api_key or os.environ.get("SENTRIAL_API_KEY")
        self.current_state: dict[str, Any] = {}
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        self._owns_client = True

    async def close(self):
        """Close the underlying HTTP client."""
        if self._owns_client and self._client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncSentrialClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Async context manager exit."""
        await self.close()
        return False

    async def create_session(
        self,
        name: str,
        agent_name: str,
        user_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Create a new session.

        Args:
            name: Name of the session
            agent_name: Required identifier for the agent type (used for grouping)
            user_id: Required external user ID (for grouping sessions by end-user)
            metadata: Optional metadata

        Returns:
            Session ID
        """
        payload = {
            "name": name,
            "agentName": agent_name,
            "userId": user_id,
            "metadata": metadata,
        }
            
        response = await self._client.post(
            f"{self.api_url}/api/sdk/sessions",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["id"]

    async def track_tool_call(
        self,
        session_id: str,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: dict[str, Any],
        reasoning: Optional[str] = None,
        estimated_cost: float = 0.0,
        tool_error: Optional[dict[str, Any]] = None,
        token_count: Optional[int] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Track a tool call event.

        Args:
            session_id: Session ID
            tool_name: Name of the tool
            tool_input: Tool input data
            tool_output: Tool output data
            reasoning: Optional reasoning for why this tool was called
            estimated_cost: Estimated cost in USD for this tool call
            tool_error: Error details if the tool failed
            token_count: Number of tokens used by this tool call
            trace_id: OpenTelemetry trace ID
            span_id: OpenTelemetry span ID
            metadata: Additional metadata

        Returns:
            Event data
        """
        state_before = self.current_state.copy()
        self.current_state[f"{tool_name}_result"] = tool_output

        payload: dict[str, Any] = {
            "sessionId": session_id,
            "eventType": EventType.TOOL_CALL.value,
            "toolName": tool_name,
            "toolInput": tool_input,
            "toolOutput": tool_output,
            "reasoning": reasoning,
            "stateBefore": state_before,
            "stateAfter": self.current_state.copy(),
            "estimatedCost": estimated_cost,
        }
        
        if tool_error is not None:
            payload["toolError"] = tool_error
        if token_count is not None:
            payload["tokenCount"] = token_count
        if trace_id is not None:
            payload["traceId"] = trace_id
        if span_id is not None:
            payload["spanId"] = span_id
        if metadata is not None:
            payload["metadata"] = metadata

        response = await self._client.post(
            f"{self.api_url}/api/sdk/events",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def track_decision(
        self,
        session_id: str,
        reasoning: str,
        alternatives: Optional[list[str]] = None,
        confidence: Optional[float] = None,
        branch_name: str = "main",
        estimated_cost: float = 0.0,
        token_count: Optional[int] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Track an LLM decision event.

        Args:
            session_id: Session ID
            reasoning: Decision reasoning
            alternatives: Alternative options considered
            confidence: Confidence score (0.0 to 1.0)
            branch_name: Branch name (default: "main")
            estimated_cost: Estimated cost in USD
            token_count: Number of tokens used
            trace_id: OpenTelemetry trace ID
            span_id: OpenTelemetry span ID
            metadata: Additional metadata

        Returns:
            Event data
        """
        state_before = self.current_state.copy()

        payload: dict[str, Any] = {
            "sessionId": session_id,
            "eventType": EventType.LLM_DECISION.value,
            "reasoning": reasoning,
            "alternativesConsidered": alternatives,
            "confidence": confidence,
            "stateBefore": state_before,
            "stateAfter": self.current_state.copy(),
            "estimatedCost": estimated_cost,
        }
        
        if token_count is not None:
            payload["tokenCount"] = token_count
        if trace_id is not None:
            payload["traceId"] = trace_id
        if span_id is not None:
            payload["spanId"] = span_id
        if metadata is not None:
            payload["metadata"] = metadata

        response = await self._client.post(
            f"{self.api_url}/api/sdk/events",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def track_error(
        self,
        session_id: str,
        error_message: str,
        error_type: Optional[str] = None,
        tool_name: Optional[str] = None,
        stack_trace: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Track an error event.

        Args:
            session_id: Session ID
            error_message: Error message
            error_type: Type of error
            tool_name: Name of the tool that caused the error
            stack_trace: Stack trace for debugging
            trace_id: OpenTelemetry trace ID
            span_id: OpenTelemetry span ID
            metadata: Additional metadata

        Returns:
            Event data
        """
        state_before = self.current_state.copy()

        error_data: dict[str, Any] = {"message": error_message}
        if error_type:
            error_data["type"] = error_type
        if stack_trace:
            error_data["stack_trace"] = stack_trace

        payload: dict[str, Any] = {
            "sessionId": session_id,
            "eventType": EventType.ERROR.value,
            "toolError": error_data,
            "stateBefore": state_before,
            "stateAfter": self.current_state.copy(),
        }
        
        if tool_name is not None:
            payload["toolName"] = tool_name
        if trace_id is not None:
            payload["traceId"] = trace_id
        if span_id is not None:
            payload["spanId"] = span_id
        if metadata is not None:
            payload["metadata"] = metadata

        response = await self._client.post(
            f"{self.api_url}/api/sdk/events",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def update_state(self, key: str, value: Any):
        """Update the current state."""
        self.current_state[key] = value

    async def complete_session(
        self, 
        session_id: str, 
        success: bool = True,
        failure_reason: Optional[str] = None,
        estimated_cost: Optional[float] = None,
        custom_metrics: Optional[Dict[str, float]] = None,
        duration_ms: Optional[int] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        user_input: Optional[str] = None,
        assistant_output: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Complete a session with performance metrics.

        Args:
            session_id: Session ID
            success: Whether the session successfully completed its goal
            failure_reason: If success=False, why did it fail?
            estimated_cost: Total estimated cost in USD
            custom_metrics: Custom KPI metrics
            duration_ms: Duration in milliseconds
            prompt_tokens: Number of prompt/input tokens used
            completion_tokens: Number of completion/output tokens used
            total_tokens: Total tokens used
            user_input: The user's original query/input
            assistant_output: The final assistant response

        Returns:
            Updated session data
        """
        payload: dict[str, Any] = {
            "status": "completed" if success else "failed",
            "success": success,
        }
        
        if failure_reason is not None:
            payload["failureReason"] = failure_reason
        if estimated_cost is not None:
            payload["estimatedCost"] = estimated_cost
        if custom_metrics is not None:
            payload["customMetrics"] = custom_metrics
        if duration_ms is not None:
            payload["durationMs"] = duration_ms
        if prompt_tokens is not None:
            payload["promptTokens"] = prompt_tokens
        if completion_tokens is not None:
            payload["completionTokens"] = completion_tokens
        if total_tokens is not None:
            payload["totalTokens"] = total_tokens
        if user_input is not None:
            payload["userInput"] = user_input
        if assistant_output is not None:
            payload["assistantOutput"] = assistant_output
        
        response = await self._client.patch(
            f"{self.api_url}/api/sdk/sessions/{session_id}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def begin(
        self,
        user_id: str,
        event: str,
        input: Optional[str] = None,
        event_id: Optional[str] = None,
        convo_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "AsyncInteraction":
        """
        Begin tracking an interaction (simplified API).

        Args:
            user_id: Required external user ID
            event: Event type/name
            input: Optional input data
            event_id: Optional custom event ID
            convo_id: Optional conversation ID
            metadata: Optional additional metadata

        Returns:
            AsyncInteraction object with finish() method
        """
        import uuid as uuid_module

        actual_event_id = event_id or str(uuid_module.uuid4())

        full_metadata = metadata.copy() if metadata else {}
        if input:
            full_metadata["input"] = input
        if convo_id:
            full_metadata["convo_id"] = convo_id
        full_metadata["event_id"] = actual_event_id

        session_id = await self.create_session(
            name=f"{event}:{actual_event_id[:8]}",
            agent_name=event,
            user_id=user_id,
            metadata=full_metadata,
        )

        return AsyncInteraction(
            client=self,
            session_id=session_id,
            event_id=actual_event_id,
            user_id=user_id,
            event=event,
            user_input=input,
        )

    # Cost calculation helpers (same as sync client)
    @staticmethod
    def calculate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for OpenAI API calls."""
        from .client import SentrialClient
        return SentrialClient.calculate_openai_cost(model, input_tokens, output_tokens)

    @staticmethod
    def calculate_anthropic_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Anthropic API calls."""
        from .client import SentrialClient
        return SentrialClient.calculate_anthropic_cost(model, input_tokens, output_tokens)

    @staticmethod
    def calculate_google_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Google/Gemini API calls."""
        from .client import SentrialClient
        return SentrialClient.calculate_google_cost(model, input_tokens, output_tokens)


class AsyncInteraction:
    """
    Represents an in-progress async interaction that can be finished.

    Supports async context manager for automatic cleanup:
        async with await client.begin(user_id="123", event="chat") as interaction:
            await interaction.track_tool_call(...)
            # Automatically finishes on exit
    """

    def __init__(
        self,
        client: AsyncSentrialClient,
        session_id: str,
        event_id: str,
        user_id: str,
        event: str,
        user_input: Optional[str] = None,
    ):
        self.client = client
        self.session_id = session_id
        self.event_id = event_id
        self.user_id = user_id
        self.event = event
        self.user_input = user_input
        self._finished = False
        self._success = True
        self._failure_reason: Optional[str] = None
        self._output: Optional[str] = None
        
        # Token tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.total_cost = 0.0

    async def __aenter__(self) -> "AsyncInteraction":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Async context manager exit - auto-finishes the interaction."""
        if not self._finished:
            if exc_type is not None:
                await self.finish(
                    success=False,
                    failure_reason=f"{exc_type.__name__}: {exc_val}" if exc_val else str(exc_type.__name__),
                )
            else:
                await self.finish(
                    success=self._success, 
                    failure_reason=self._failure_reason,
                    output=self._output,
                )
        return False

    def add_tokens(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
    ):
        """
        Add token counts (auto-summed across calls).
        
        Args:
            prompt_tokens: Number of prompt/input tokens
            completion_tokens: Number of completion/output tokens
            cost: Cost in USD
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.total_cost += cost

    def set_output(self, output: str):
        """Set the output for when context manager exits."""
        self._output = output

    async def finish(
        self,
        output: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        estimated_cost: Optional[float] = None,
        custom_metrics: Optional[Dict[str, float]] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Finish the interaction and record metrics.

        Args:
            output: Output/response from the interaction
            success: Whether the interaction succeeded
            failure_reason: Reason for failure if success=False
            estimated_cost: Total estimated cost (uses accumulated if not provided)
            custom_metrics: Custom KPI metrics
            prompt_tokens: Number of prompt tokens (uses accumulated if not provided)
            completion_tokens: Number of completion tokens (uses accumulated if not provided)
            total_tokens: Total tokens (uses accumulated if not provided)

        Returns:
            Updated session data
        """
        if self._finished:
            raise RuntimeError("Interaction already finished")

        self._finished = True

        # Use accumulated values if not explicitly provided
        final_cost = estimated_cost if estimated_cost is not None else (self.total_cost if self.total_cost > 0 else None)
        final_prompt = prompt_tokens if prompt_tokens is not None else (self.total_prompt_tokens if self.total_prompt_tokens > 0 else None)
        final_completion = completion_tokens if completion_tokens is not None else (self.total_completion_tokens if self.total_completion_tokens > 0 else None)
        final_total = total_tokens if total_tokens is not None else (self.total_tokens if self.total_tokens > 0 else None)

        return await self.client.complete_session(
            session_id=self.session_id,
            success=success,
            failure_reason=failure_reason,
            estimated_cost=final_cost,
            custom_metrics=custom_metrics,
            prompt_tokens=final_prompt,
            completion_tokens=final_completion,
            total_tokens=final_total,
            user_input=self.user_input,
            assistant_output=output or self._output,
        )

    async def track_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: dict[str, Any],
        reasoning: Optional[str] = None,
        estimated_cost: float = 0.0,
        tool_error: Optional[dict[str, Any]] = None,
        token_count: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Track a tool call within this interaction."""
        return await self.client.track_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            reasoning=reasoning,
            estimated_cost=estimated_cost,
            tool_error=tool_error,
            token_count=token_count,
            metadata=metadata,
        )

    async def track_decision(
        self,
        reasoning: str,
        alternatives: Optional[list[str]] = None,
        confidence: Optional[float] = None,
        estimated_cost: float = 0.0,
        token_count: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Track an LLM decision within this interaction."""
        return await self.client.track_decision(
            session_id=self.session_id,
            reasoning=reasoning,
            alternatives=alternatives,
            confidence=confidence,
            estimated_cost=estimated_cost,
            token_count=token_count,
            metadata=metadata,
        )

    async def track_error(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        tool_name: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Track an error within this interaction."""
        self._success = False
        self._failure_reason = error_message
        
        return await self.client.track_error(
            session_id=self.session_id,
            error_message=error_message,
            error_type=error_type,
            tool_name=tool_name,
            stack_trace=stack_trace,
            metadata=metadata,
        )


# Module-level async client instance
_default_async_client: Optional[AsyncSentrialClient] = None


async def _get_async_client() -> AsyncSentrialClient:
    """Get or create the default async client instance."""
    global _default_async_client
    if _default_async_client is None:
        _default_async_client = AsyncSentrialClient()
    return _default_async_client


async def configure_async(api_key: Optional[str] = None, api_url: Optional[str] = None) -> None:
    """
    Configure the default async Sentrial client.

    Args:
        api_key: API key for authentication
        api_url: URL of the Sentrial API server
    """
    global _default_async_client
    if _default_async_client:
        await _default_async_client.close()
    _default_async_client = AsyncSentrialClient(api_key=api_key, api_url=api_url)


async def begin_async(
    user_id: str,
    event: str,
    input: Optional[str] = None,
    event_id: Optional[str] = None,
    convo_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AsyncInteraction:
    """
    Begin tracking an async interaction (module-level convenience function).

    Example:
        import sentrial
        from sentrial.async_client import begin_async

        interaction = await begin_async(
            user_id='user_123',
            event='chat_message',
            input=message
        )

        # ... do your async agent work ...

        await interaction.finish(output=response_text)
    """
    client = await _get_async_client()
    return await client.begin(
        user_id=user_id,
        event=event,
        input=input,
        event_id=event_id,
        convo_id=convo_id,
        metadata=metadata,
    )
