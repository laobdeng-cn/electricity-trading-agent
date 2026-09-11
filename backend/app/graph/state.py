from typing import Any, TypedDict

from app.schemas.agent import AgentToolExecution


class MarketAgentState(TypedDict):
    """LangGraph state shared by the market-agent nodes."""

    messages: list[dict[str, Any]]
    tool_executions: list[AgentToolExecution]
    final_answer: str | None
    steps: int
