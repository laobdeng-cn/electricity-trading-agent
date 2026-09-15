from typing import Any

from pydantic import BaseModel, Field


class MultiAgentAnalyzeRequest(BaseModel):
    market_data_id: int = Field(ge=1)


class MultiAgentAnalyzeResponse(BaseModel):
    market_analysis: dict[str, Any]
    risk_analysis: dict[str, Any]
    decision: dict[str, Any]
    visited_agents: list[str]
    final_answer: str | None
