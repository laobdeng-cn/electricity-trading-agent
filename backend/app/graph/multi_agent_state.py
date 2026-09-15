from typing import Any, TypedDict


class MultiAgentState(TypedDict):
    """Shared state for the first multi-agent workflow prototype."""

    request: str
    market_analysis: dict[str, Any] | None
    risk_analysis: dict[str, Any] | None
    final_answer: str | None
    visited_agents: list[str]
