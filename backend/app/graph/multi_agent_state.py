from typing import Any, Literal, TypedDict


AgentExecutionStatus = Literal["success", "fallback", "failed"]


class MultiAgentState(TypedDict):
    """Shared state for the multi-agent workflow prototype."""

    request: str
    workflow_id: str
    workflow_started_at: str
    workflow_completed_at: str | None
    market_analysis: dict[str, Any] | None
    risk_analysis: dict[str, Any] | None
    decision_analysis: dict[str, Any] | None
    explanation: str | None
    explanation_status: Literal["llm", "fallback"] | None
    explanation_model: str | None
    explanation_latency_ms: float | None
    explanation_error: str | None
    workflow_latency_ms: float | None
    agent_latency_ms: dict[str, float]
    agent_status: dict[str, AgentExecutionStatus]
    final_answer: str | None
    visited_agents: list[str]
