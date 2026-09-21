from typing import Any, Literal

from pydantic import BaseModel, Field


AgentExecutionStatus = Literal["success", "fallback", "failed"]


class MultiAgentAnalyzeRequest(BaseModel):
    market_data_id: int = Field(ge=1)


class MultiAgentAnalyzeResponse(BaseModel):
    workflow_id: str
    workflow_started_at: str
    workflow_completed_at: str
    market_analysis: dict[str, Any]
    risk_analysis: dict[str, Any]
    decision: dict[str, Any]
    explanation: str | None = None
    explanation_status: Literal["llm", "fallback"] | None = None
    explanation_model: str | None = None
    explanation_latency_ms: float | None = None
    explanation_error: str | None = None
    workflow_latency_ms: float | None = None
    agent_latency_ms: dict[str, float] = Field(default_factory=dict)
    agent_status: dict[str, AgentExecutionStatus] = Field(default_factory=dict)
    visited_agents: list[str]
    final_answer: str | None
