from typing import Any

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AnalyzeMarketToolArgs(BaseModel):
    market_data_id: int = Field(gt=0)


class AgentToolExecution(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class AgentChatResponse(BaseModel):
    answer: str
    model: str
    tool_executions: list[AgentToolExecution] = Field(default_factory=list)
