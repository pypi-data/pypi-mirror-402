"""LangChain integration for Sentrial observability."""

from typing import Any, Dict, List, Optional
from uuid import UUID
import time

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.agents import AgentAction, AgentFinish
    from langchain_core.outputs import LLMResult
except ImportError:
    raise ImportError(
        "LangChain is required for this integration. "
        "Install it with: pip install langchain-core"
    )

from .client import SentrialClient

# Pricing per 1K tokens (as of Jan 2026)
# Format: {model_prefix: (input_cost_per_1k, output_cost_per_1k)}
MODEL_PRICING = {
    # OpenAI - Latest models
    "gpt-5.2": (0.005, 0.015),
    "gpt-5": (0.004, 0.012),
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "o3": (0.01, 0.04),
    "o3-mini": (0.003, 0.012),
    "o1-preview": (0.015, 0.06),
    "o1-mini": (0.003, 0.012),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-4": (0.03, 0.06),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    # Anthropic - Latest models
    "claude-4.5-opus": (0.02, 0.1),
    "claude-4.5-sonnet": (0.004, 0.02),
    "claude-4-opus": (0.018, 0.09),
    "claude-4-sonnet": (0.0035, 0.0175),
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    # Google Gemini 3 - Preview models (Jan 2026)
    "gemini-3-pro": (0.002, 0.012),
    "gemini-3-flash": (0.0005, 0.003),
    # Google Gemini 2.5
    "gemini-2.5-pro": (0.00125, 0.005),
    "gemini-2.5-flash": (0.00015, 0.0006),
    # Google Gemini 2.0
    "gemini-2.0-flash": (0.0001, 0.0004),
    "gemini-2.0-flash-lite": (0.000075, 0.0003),
    # Google Gemini 1.5
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-1.5-flash": (0.000075, 0.0003),
    # Default fallback
    "default": (0.001, 0.002),
}


def get_model_pricing(model_name: str) -> tuple[float, float]:
    """Get pricing for a model. Returns (input_cost_per_1k, output_cost_per_1k)."""
    if not model_name:
        return MODEL_PRICING["default"]
    
    model_lower = model_name.lower()
    
    # Try exact match first, then prefix match
    for prefix, pricing in MODEL_PRICING.items():
        if prefix in model_lower:
            return pricing
    
    return MODEL_PRICING["default"]


def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate actual cost based on token usage and model pricing."""
    input_price, output_price = get_model_pricing(model_name)
    
    input_cost = (prompt_tokens / 1000) * input_price
    output_cost = (completion_tokens / 1000) * output_price
    
    return round(input_cost + output_cost, 6)


class SentrialCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for Sentrial performance monitoring.
    
    Automatically tracks:
    - Agent reasoning (Chain of Thought)
    - Tool executions (with inputs/outputs)
    - Tool errors
    - LLM calls with REAL token usage and cost
    
    Usage:
        from sentrial import SentrialClient
        from sentrial.langchain import SentrialCallbackHandler
        
        client = SentrialClient(api_url="...", project_id="...")
        session_id = client.create_session(name="My Agent Run", agent_name="my_agent")
        handler = SentrialCallbackHandler(client, session_id)
        
        # Pass to LangChain agent
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            callbacks=[handler],
            verbose=True
        )
        
        # After agent finishes, get actual costs
        print(f"Total cost: ${handler.total_cost:.4f}")
        print(f"Tokens used: {handler.total_tokens}")
    """
    
    def __init__(
        self, 
        client: SentrialClient, 
        session_id: str,
        track_llm_calls: bool = True,  # Default to True now
        verbose: bool = False
    ):
        """
        Initialize Sentrial callback handler.
        
        Args:
            client: SentrialClient instance
            session_id: Active session ID
            track_llm_calls: Whether to track individual LLM API calls (default: True)
            verbose: Print tracking info (default: False)
        """
        super().__init__()
        self.client = client
        self.session_id = session_id
        self.track_llm_calls = track_llm_calls
        self.verbose = verbose
        
        # Track tool runs in flight (run_id -> tool data)
        self.tool_runs: Dict[str, Dict[str, Any]] = {}
        
        # Track pending agent actions (for correlating with tool outputs)
        self.pending_actions: Dict[str, Dict[str, Any]] = {}
        
        # Track agent steps
        self.step_count = 0
        
        # Track last LLM output for reasoning
        self.last_llm_reasoning: Optional[str] = None
        
        # Token and cost tracking (REAL data from LLM responses)
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.llm_calls = 0
        self.model_name: Optional[str] = None
        
        # Automatic duration tracking
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # User input/output tracking (for Raindrop-style display)
        self.user_input: Optional[str] = None
        self.assistant_output: Optional[str] = None
    
    def set_input(self, user_input: str) -> None:
        """
        Set the user's original input/query for this session.
        
        Call this before running the agent to track the user's query.
        
        Args:
            user_input: The user's original question/query
            
        Example:
            handler = SentrialCallbackHandler(client, session_id)
            handler.set_input("What's the weather in San Francisco?")
            agent_executor.invoke({"input": user_input}, callbacks=[handler])
        """
        self.user_input = user_input
        self._log(f"User input set: {user_input[:50]}...")
    
    def _log(self, message: str):
        """Log if verbose mode is enabled."""
        if self.verbose:
            print(f"[Sentrial] {message}")
    
    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds (automatically tracked)."""
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time else time.time()
        return int((end - self.start_time) * 1000)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of token usage, costs, and duration for this session."""
        return {
            "llm_calls": self.llm_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "model": self.model_name,
            "duration_ms": self.duration_ms,
        }
    
    # ===== Agent Reasoning (Chain of Thought) =====
    
    def on_agent_action(
        self, 
        action: AgentAction, 
        *, 
        run_id: UUID, 
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """
        Capture agent reasoning - tool will be tracked in on_tool_end with actual output.
        """
        self.step_count += 1
        reasoning = action.log if action.log else f"Action: {action.tool}"
        tool_name = action.tool
        tool_input = action.tool_input
        
        self._log(f"Step {self.step_count}: Agent action - {tool_name}")
        
        # Store the pending action for correlation with tool output in on_tool_end
        # Don't track here - wait for on_tool_end to get the actual output
        self.pending_actions[str(run_id)] = {
            "tool": tool_name,
            "input": tool_input,
            "reasoning": reasoning,
            "tracked": False,
            "step_number": self.step_count
        }
    
    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Track agent completion and capture assistant output."""
        self._log("Agent finished")
        
        # Capture assistant output for session summary
        output = finish.return_values.get('output', 'No output')
        self.assistant_output = output
        
        self.client.track_decision(
            session_id=self.session_id,
            reasoning=f"Agent completed: {output}",
            confidence=1.0
        )
    
    # ===== Tool Execution =====
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Buffer tool inputs for correlation with outputs."""
        tool_name = serialized.get("name", "unknown_tool")
        
        self._log(f"Tool started: {tool_name}")
        
        # Check if we have a pending action for this tool
        parent_id = str(parent_run_id) if parent_run_id else None
        pending = None
        if parent_id and parent_id in self.pending_actions:
            pending = self.pending_actions.get(parent_id)
        
        self.tool_runs[str(run_id)] = {
            "name": tool_name,
            "input": input_str,
            "pending_action": pending,
            "parent_run_id": parent_id
        }
    
    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Track successful tool execution with full input/output."""
        run_data = self.tool_runs.pop(str(run_id), None)
        
        # Get pending action data if available (from on_agent_action)
        parent_id = str(parent_run_id) if parent_run_id else None
        pending = None
        if parent_id and parent_id in self.pending_actions:
            pending = self.pending_actions.get(parent_id)
            # Mark as tracked now
            if pending:
                pending["tracked"] = True
        
        # Get tool name and input - prefer pending action data, fall back to run_data
        if pending:
            tool_name = pending["tool"]
            tool_input = pending["input"]
            reasoning = pending.get("reasoning")
        elif run_data:
            tool_name = run_data["name"]
            tool_input = run_data["input"]
            # Use the last captured reasoning from LLM if no pending action
            reasoning = self.last_llm_reasoning
            self.last_llm_reasoning = None
        else:
            self._log("Tool ended but no run data found")
            return
        
        self._log(f"Tool completed: {tool_name}")
        
        # Safely serialize output (might be ToolMessage or other object)
        if isinstance(output, str):
            output_value = output
        elif hasattr(output, 'content'):
            # ToolMessage object
            output_value = str(output.content)
        elif hasattr(output, '__dict__'):
            # Try to get a reasonable string representation
            output_value = str(output)
        else:
            output_value = str(output)
        
        # Parse input/output
        input_dict = tool_input if isinstance(tool_input, dict) else {"input": str(tool_input) if tool_input else ""}
        output_dict = {"output": output_value}
        
        self.client.track_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            tool_input=input_dict,
            tool_output=output_dict,
            reasoning=reasoning,
        )
    
    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Track tool errors."""
        run_data = self.tool_runs.pop(str(run_id), None)
        
        if run_data:
            tool_name = run_data["name"]
            tool_input = run_data["input"]
            
            self._log(f"Tool error: {tool_name} - {error}")
            
            input_dict = {"input": tool_input} if isinstance(tool_input, str) else tool_input
            
            self.client.track_tool_call(
                session_id=self.session_id,
                tool_name=tool_name,
                tool_input=input_dict,
                tool_output={"error": str(error), "error_type": type(error).__name__},
            )
    
    # ===== LLM Calls - Now tracks REAL token usage and costs =====
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Track LLM call start and auto-track duration."""
        # Start timing on first LLM call
        if self.start_time is None:
            self.start_time = time.time()
        
        self._log(f"LLM call started: {len(prompts)} prompts")
    
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """
        Track LLM responses with REAL token usage and costs.
        
        Extracts actual usage data from the LLM response.
        """
        self.llm_calls += 1
        
        # Extract token usage - check multiple locations since different providers structure it differently
        prompt_tokens = 0
        completion_tokens = 0
        
        # 1. Check llm_output (OpenAI style)
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {}) or llm_output.get("usage", {})
        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens", 0) or token_usage.get("input_tokens", 0) or 0
            completion_tokens = token_usage.get("completion_tokens", 0) or token_usage.get("output_tokens", 0) or 0
        
        # 2. Check generation.message.usage_metadata (Gemini, newer LangChain)
        if not (prompt_tokens or completion_tokens) and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    # ChatGeneration has .message which is AIMessage with usage_metadata
                    if hasattr(gen, 'message') and hasattr(gen.message, 'usage_metadata'):
                        usage_meta = gen.message.usage_metadata
                        if usage_meta:
                            prompt_tokens = usage_meta.get('input_tokens', 0) or usage_meta.get('prompt_tokens', 0) or 0
                            completion_tokens = usage_meta.get('output_tokens', 0) or usage_meta.get('completion_tokens', 0) or 0
                            break
                if prompt_tokens or completion_tokens:
                    break
        
        # Get model name from llm_output or generation_info
        model_name = llm_output.get("model_name") or llm_output.get("model") or ""
        if not model_name and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, 'generation_info') and gen.generation_info:
                        model_name = gen.generation_info.get('model_name', '')
                        break
        if model_name:
            self.model_name = model_name
        
        # Calculate cost for this call
        call_cost = calculate_cost(model_name, prompt_tokens, completion_tokens)
        
        # Accumulate totals
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.total_cost += call_cost
        
        # Update end time on every LLM call (last one will be the final end time)
        self.end_time = time.time()
        
        self._log(
            f"LLM call completed: {prompt_tokens} in, {completion_tokens} out, "
            f"${call_cost:.4f} (total: ${self.total_cost:.4f})"
        )
        
        # Extract reasoning from the LLM output for the next tool call
        if response.generations and len(response.generations) > 0:
            generation = response.generations[0][0]
            if hasattr(generation, 'text'):
                text = generation.text
                # Try to extract "Thought:" from the output
                if 'Thought:' in text:
                    thought_start = text.find('Thought:') + len('Thought:')
                    thought_end = text.find('Action:', thought_start)
                    if thought_end == -1:
                        thought_end = text.find('Final Answer:', thought_start)
                    if thought_end == -1:
                        thought_end = len(text)
                    reasoning = text[thought_start:thought_end].strip()
                    self.last_llm_reasoning = reasoning
    
    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Track LLM errors."""
        self._log(f"LLM error: {error}")

    # ===== Session Completion =====

    def finish(
        self,
        success: bool = True,
        failure_reason: Optional[str] = None,
        custom_metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Finish the session and record final metrics.
        
        Automatically includes tracked token usage and costs.
        
        Args:
            success: Whether the agent run succeeded
            failure_reason: Reason for failure if success=False
            custom_metrics: Additional custom KPI metrics
            
        Returns:
            Updated session data
            
        Example:
            handler = SentrialCallbackHandler(client, session_id)
            # ... run agent with handler ...
            result = handler.finish(
                success=True,
                custom_metrics={"quality": 4.5}
            )
            print(f"Total cost: ${handler.total_cost:.4f}")
        """
        return self.client.complete_session(
            session_id=self.session_id,
            success=success,
            failure_reason=failure_reason,
            estimated_cost=self.total_cost,
            custom_metrics=custom_metrics,
            duration_ms=self.duration_ms,
            prompt_tokens=self.total_prompt_tokens,
            completion_tokens=self.total_completion_tokens,
            total_tokens=self.total_tokens,
            user_input=self.user_input,
            assistant_output=self.assistant_output,
        )
