"""Sentrial Client - Main SDK interface"""

import os
import requests
from typing import Any, Optional, Dict
from .types import EventType


class SentrialClient:
    """
    Sentrial Client for tracking agent performance and KPIs.

    Usage:
        client = SentrialClient(
            api_key="sentrial_live_xxx",
            api_url="https://api.sentrial.com"
        )

        # Create a session for an agent run
        session_id = client.create_session(
            name="Support Request #123",
            agent_name="support-agent"
        )

        # Track events
        client.track_tool_call(
            session_id=session_id,
            tool_name="search_kb",
            tool_input={"query": "password reset"},
            tool_output={"articles": ["KB-001"]}
        )

        # Complete session with metrics
        client.complete_session(
            session_id=session_id,
            success=True,
            custom_metrics={"customer_satisfaction": 90}
        )
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Sentrial client.

        Args:
            api_url: URL of the Sentrial API server (defaults to SENTRIAL_API_URL env var or production)
            api_key: API key for authentication (defaults to SENTRIAL_API_KEY env var)
        """
        self.api_url = (api_url or os.environ.get("SENTRIAL_API_URL", "https://api.sentrial.com")).rstrip("/")
        self.api_key = api_key or os.environ.get("SENTRIAL_API_KEY")
        self.session = requests.Session()
        self.current_state: dict[str, Any] = {}

        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def create_session(
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
            
        response = self.session.post(
            f"{self.api_url}/api/sdk/sessions",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["id"]

    def track_tool_call(
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
            tool_error: Error details if the tool failed (e.g., {"message": "...", "type": "..."})
            token_count: Number of tokens used by this tool call (for LLM-based tools)
            trace_id: OpenTelemetry trace ID for distributed tracing
            span_id: OpenTelemetry span ID for distributed tracing
            metadata: Additional metadata to attach to this event

        Returns:
            Event data
        """
        state_before = self.current_state.copy()

        # Update current state (simplified)
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

        response = self.session.post(
            f"{self.api_url}/api/sdk/events",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def track_decision(
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
            estimated_cost: Estimated cost in USD for this decision
            token_count: Number of tokens used
            trace_id: OpenTelemetry trace ID for distributed tracing
            span_id: OpenTelemetry span ID for distributed tracing
            metadata: Additional metadata to attach to this event

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

        response = self.session.post(
            f"{self.api_url}/api/sdk/events",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def track_error(
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
            error_type: Type of error (e.g., "ValueError", "APIError")
            tool_name: Name of the tool that caused the error (if applicable)
            stack_trace: Stack trace for debugging
            trace_id: OpenTelemetry trace ID for distributed tracing
            span_id: OpenTelemetry span ID for distributed tracing
            metadata: Additional metadata to attach to this event

        Returns:
            Event data
        """
        state_before = self.current_state.copy()

        error_data: dict[str, Any] = {
            "message": error_message,
        }
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

        response = self.session.post(
            f"{self.api_url}/api/sdk/events",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def update_state(self, key: str, value: Any):
        """Update the current state."""
        self.current_state[key] = value

    def complete_session(
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

        This is the recommended way to close sessions for performance monitoring.

        Args:
            session_id: Session ID
            success: Whether the session successfully completed its goal (default: True)
            failure_reason: If success=False, why did it fail?
            estimated_cost: Total estimated cost in USD for this session
            custom_metrics: Custom KPI metrics (e.g., {"customer_satisfaction": 4.5, "order_value": 129.99})
            duration_ms: Duration in milliseconds (auto-calculated if not provided)
            prompt_tokens: Number of prompt/input tokens used
            completion_tokens: Number of completion/output tokens used
            total_tokens: Total tokens used (prompt + completion)
            user_input: The user's original query/input for this session
            assistant_output: The final assistant response for this session

        Returns:
            Updated session data

        Example:
            >>> client.complete_session(
            ...     session_id=session_id,
            ...     success=True,
            ...     estimated_cost=0.023,
            ...     prompt_tokens=1500,
            ...     completion_tokens=500,
            ...     total_tokens=2000,
            ...     user_input="What's the weather in San Francisco?",
            ...     assistant_output="The weather in San Francisco is 65°F and sunny.",
            ...     custom_metrics={
            ...         "customer_satisfaction": 4.5,
            ...         "order_value": 129.99,
            ...         "items_processed": 7
            ...     }
            ... )
        """
        payload = {
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
        
        response = self.session.patch(
            f"{self.api_url}/api/sdk/sessions/{session_id}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def close_session(
        self,
        session_id: str,
        duration_ms: Optional[int] = None,
        success: Optional[bool] = None,
        failure_reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Mark a session as completed (legacy method).

        Note: Use complete_session() for better performance monitoring with custom metrics.

        Args:
            session_id: Session ID
            duration_ms: Duration in milliseconds
            success: Whether the session successfully completed its goal
            failure_reason: If success=False, why did it fail?

        Returns:
            Updated session data
        """
        return self.complete_session(
            session_id=session_id,
            success=success if success is not None else True,
            failure_reason=failure_reason,
            duration_ms=duration_ms,
        )

    # Cost calculation helpers
    @staticmethod
    def calculate_openai_cost(
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate cost for OpenAI API calls.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD

        Example:
            >>> cost = SentrialClient.calculate_openai_cost(
            ...     model="gpt-4",
            ...     input_tokens=1000,
            ...     output_tokens=500
            ... )
            >>> print(f"Cost: ${cost:.4f}")
        """
        # Pricing as of 2026 (per 1M tokens)
        pricing = {
            "gpt-5.2": {"input": 5.0, "output": 15.0},
            "gpt-5": {"input": 4.0, "output": 12.0},
            "gpt-4o": {"input": 2.5, "output": 10.0},
            "gpt-4o-mini": {"input": 0.15, "output": 0.6},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "o3": {"input": 10.0, "output": 40.0},
            "o3-mini": {"input": 3.0, "output": 12.0},
            "o1-preview": {"input": 15.0, "output": 60.0},
            "o1-mini": {"input": 3.0, "output": 12.0},
        }

        # Find matching model (handle versioned models like gpt-4-0613)
        model_key = None
        for key in pricing.keys():
            if model.startswith(key):
                model_key = key
                break

        if not model_key:
            # Default to gpt-4 pricing if unknown
            model_key = "gpt-4"

        rates = pricing[model_key]
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost

    @staticmethod
    def calculate_anthropic_cost(
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate cost for Anthropic API calls.

        Args:
            model: Model name (e.g., "claude-3-opus", "claude-3-sonnet")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pricing = {
            "claude-4.5-opus": {"input": 20.0, "output": 100.0},
            "claude-4.5-sonnet": {"input": 4.0, "output": 20.0},
            "claude-4-opus": {"input": 18.0, "output": 90.0},
            "claude-4-sonnet": {"input": 3.5, "output": 17.5},
            "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
        }

        model_key = None
        for key in pricing.keys():
            if model.startswith(key):
                model_key = key
                break

        if not model_key:
            model_key = "claude-3-sonnet"

        rates = pricing[model_key]
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost

    @staticmethod
    def calculate_google_cost(
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate cost for Google/Gemini API calls.

        Args:
            model: Model name (e.g., "gemini-3-pro-preview", "gemini-2.5-flash")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Pricing as of Jan 2026 (per 1M tokens)
        pricing = {
            # Gemini 3 - Preview (Jan 2026)
            "gemini-3-pro": {"input": 2.0, "output": 12.0},
            "gemini-3-flash": {"input": 0.5, "output": 3.0},
            # Gemini 2.5
            "gemini-2.5-pro": {"input": 1.25, "output": 5.0},
            "gemini-2.5-flash": {"input": 0.15, "output": 0.6},
            # Gemini 2.0
            "gemini-2.0-flash": {"input": 0.1, "output": 0.4},
            "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.3},
            # Gemini 1.5
            "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
            # Gemini 1.0
            "gemini-1.0-pro": {"input": 0.5, "output": 1.5},
        }

        model_key = None
        for key in pricing.keys():
            if model.startswith(key):
                model_key = key
                break

        if not model_key:
            model_key = "gemini-2.0-flash"

        rates = pricing[model_key]
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost

    def begin(
        self,
        user_id: str,
        event: str,
        input: Optional[str] = None,
        event_id: Optional[str] = None,
        convo_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "Interaction":
        """
        Begin tracking an interaction (simplified API).

        Args:
            user_id: Required external user ID for grouping sessions
            event: Event type/name (e.g., "chat_message", "search_query")
            input: Optional input data for the interaction
            event_id: Optional custom event ID (auto-generated UUID if not provided)
            convo_id: Optional conversation ID to group related interactions
            metadata: Optional additional metadata

        Returns:
            Interaction object with finish() method

        Example:
            interaction = client.begin(
                user_id='user_123',
                event='chat_message',
                input=message,
                convo_id='convo_456'
            )

            # ... do your agent work ...

            interaction.finish(output=response_text)
        
        With context manager (recommended for auto-tracking):
            with client.begin(user_id='user_123', event='chat', input=message) as interaction:
                # Any wrapped LLM calls (wrap_openai, etc.) are auto-tracked!
                response = openai_client.chat.completions.create(...)
                interaction.set_output(response.choices[0].message.content)
                # Automatically finishes on exit
        """
        import uuid as uuid_module

        actual_event_id = event_id or str(uuid_module.uuid4())

        # Store input in current_state for later retrieval
        if input:
            self.current_state["input"] = input

        # Build metadata with optional fields
        full_metadata = metadata.copy() if metadata else {}
        if input:
            full_metadata["input"] = input
        if convo_id:
            full_metadata["convo_id"] = convo_id
        full_metadata["event_id"] = actual_event_id

        session_id = self.create_session(
            name=f"{event}:{actual_event_id[:8]}",
            agent_name=event,
            user_id=user_id,
            metadata=full_metadata,
        )

        return Interaction(
            client=self,
            session_id=session_id,
            event_id=actual_event_id,
            user_id=user_id,
            event=event,
        )


class Interaction:
    """
    Represents an in-progress interaction that can be finished.

    Created by SentrialClient.begin() - provides a clean begin/finish API pattern.
    
    Supports context manager for automatic cleanup:
        with client.begin(user_id="123", event="chat") as interaction:
            interaction.track_tool_call(...)
            # Automatically finishes on exit
    
    Auto-tracks wrapped LLM clients:
        When used as a context manager, any LLM calls made with wrapped clients
        (wrap_openai, wrap_anthropic, wrap_google) are automatically associated
        with this session.
    """

    def __init__(
        self,
        client: SentrialClient,
        session_id: str,
        event_id: str,
        user_id: str,
        event: str,
    ):
        self.client = client
        self.session_id = session_id
        self.event_id = event_id
        self.user_id = user_id
        self.event = event
        self._finished = False
        self._success = True
        self._failure_reason: Optional[str] = None
        self._output: Optional[str] = None
        
        # Accumulated metrics from wrapped LLM calls
        self._total_tokens = 0
        self._total_cost = 0.0

    def __enter__(self) -> "Interaction":
        """Context manager entry - sets up session context for auto-tracking."""
        # Import here to avoid circular imports
        from .wrappers import set_session_context
        set_session_context(self.session_id, self.client)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Context manager exit - auto-finishes the interaction and clears context."""
        # Clear the session context
        from .wrappers import clear_session_context
        clear_session_context()
        
        if not self._finished:
            if exc_type is not None:
                # An exception occurred - mark as failed
                self.finish(
                    success=False,
                    failure_reason=f"{exc_type.__name__}: {exc_val}" if exc_val else str(exc_type.__name__),
                )
            else:
                # Normal exit - finish with stored success status
                self.finish(
                    output=self._output,
                    success=self._success, 
                    failure_reason=self._failure_reason
                )
        return False  # Don't suppress exceptions
    
    def set_output(self, output: str) -> None:
        """
        Set the output for this interaction.
        
        This will be used when the context manager exits.
        Useful when you don't want to call finish() explicitly.
        
        Args:
            output: The output/response text
        """
        self._output = output

    def finish(
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
            success: Whether the interaction succeeded (default: True)
            failure_reason: Reason for failure if success=False
            estimated_cost: Total estimated cost in USD
            custom_metrics: Custom KPI metrics
            prompt_tokens: Number of prompt/input tokens used
            completion_tokens: Number of completion/output tokens used
            total_tokens: Total tokens used

        Returns:
            Updated session data

        Example:
            interaction.finish(
                output="Here's the answer to your question...",
                success=True,
                custom_metrics={"satisfaction": 4.5}
            )
        """
        if self._finished:
            raise RuntimeError("Interaction already finished")

        self._finished = True

        # Use stored output if not provided
        final_output = output or self._output

        # Merge output into custom_metrics if provided
        metrics = custom_metrics.copy() if custom_metrics else {}

        # Get input from session metadata if available
        user_input = self.client.current_state.get("input")

        return self.client.complete_session(
            session_id=self.session_id,
            success=success,
            failure_reason=failure_reason,
            estimated_cost=estimated_cost,
            custom_metrics=metrics if metrics else None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            user_input=user_input,
            assistant_output=final_output,
        )

    def track_tool_call(
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
        return self.client.track_tool_call(
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

    def track_decision(
        self,
        reasoning: str,
        alternatives: Optional[list[str]] = None,
        confidence: Optional[float] = None,
        estimated_cost: float = 0.0,
        token_count: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Track an LLM decision within this interaction."""
        return self.client.track_decision(
            session_id=self.session_id,
            reasoning=reasoning,
            alternatives=alternatives,
            confidence=confidence,
            estimated_cost=estimated_cost,
            token_count=token_count,
            metadata=metadata,
        )

    def track_error(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        tool_name: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Track an error within this interaction."""
        # Store failure info for context manager exit
        self._success = False
        self._failure_reason = error_message
        
        return self.client.track_error(
            session_id=self.session_id,
            error_message=error_message,
            error_type=error_type,
            tool_name=tool_name,
            stack_trace=stack_trace,
            metadata=metadata,
        )


# Module-level client instance for simple API
_default_client: Optional[SentrialClient] = None


def _get_client() -> SentrialClient:
    """Get or create the default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = SentrialClient()
    return _default_client


def configure(api_key: Optional[str] = None, api_url: Optional[str] = None) -> None:
    """
    Configure the default Sentrial client.

    Args:
        api_key: API key for authentication
        api_url: URL of the Sentrial API server
    """
    global _default_client
    _default_client = SentrialClient(api_key=api_key, api_url=api_url)


def begin(
    user_id: str,
    event: str,
    input: Optional[str] = None,
    event_id: Optional[str] = None,
    convo_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Interaction:
    """
    Begin tracking an interaction (module-level convenience function).

    This is a shorthand for SentrialClient().begin(...).
    Configure the client first with sentrial.configure() or set SENTRIAL_API_KEY env var.

    Args:
        user_id: Required external user ID for grouping sessions
        event: Event type/name (e.g., "chat_message", "search_query")
        input: Optional input data for the interaction
        event_id: Optional custom event ID (auto-generated UUID if not provided)
        convo_id: Optional conversation ID to group related interactions
        metadata: Optional additional metadata

    Returns:
        Interaction object with finish() method

    Example:
        import sentrial

        sentrial.configure(api_key="sentrial_live_xxx")

        interaction = sentrial.begin(
            user_id='user_123',
            event='chat_message',
            input=message
        )

        # ... do your agent work ...

        interaction.finish(output=response_text)
    """
    return _get_client().begin(
        user_id=user_id,
        event=event,
        input=input,
        event_id=event_id,
        convo_id=convo_id,
        metadata=metadata,
    )

