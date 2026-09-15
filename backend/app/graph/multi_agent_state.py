from typing import Any, Literal, TypedDict


class MultiAgentState(TypedDict):
    """Shared state for the multi-agent workflow prototype."""

    request: str
    market_analysis: dict[str, Any] | None
    risk_analysis: dict[str, Any] | None
    decision_analysis: dict[str, Any] | None
    explanation: str | None
    explanation_status: Literal["llm", "fallback"] | None
    explanation_model: str | None
    explanation_latency_ms: float | None
    explanation_error: str | None
    final_answer: str | None
    visited_agents: list[str]
