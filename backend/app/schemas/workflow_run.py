from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: str
    market_data_id: int
    started_at: datetime
    completed_at: datetime | None
    workflow_latency_ms: float | None
    status: str
    failed_agent: str | None
    error_type: str | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunPageResponse(BaseModel):
    items: list[WorkflowRunResponse]
    total: int
    limit: int
    offset: int


class WorkflowRunStatsResponse(BaseModel):
    total: int
    success: int
    failed: int
    average_latency_ms: float | None
