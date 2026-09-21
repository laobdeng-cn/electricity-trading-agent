from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.market_analyst import MarketDataNotFoundError
from app.core.dependencies import get_db, get_multi_agent_runner
from app.graph.multi_agent_graph import (
    MultiAgentGraphRunner,
    WorkflowExecutionError,
)
from app.repositories.workflow_run import WorkflowRunRepository
from app.schemas.multi_agent import (
    MultiAgentAnalyzeRequest,
    MultiAgentAnalyzeResponse,
)


router = APIRouter(
    prefix="/multi-agent",
    tags=["Multi Agent"],
)


@router.post(
    "/analyze",
    response_model=MultiAgentAnalyzeResponse,
)
def analyze_with_multi_agent(
    payload: MultiAgentAnalyzeRequest,
    runner: Annotated[
        MultiAgentGraphRunner,
        Depends(get_multi_agent_runner),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> MultiAgentAnalyzeResponse:
    try:
        state = runner.run(f"分析市场数据 {payload.market_data_id}")
    except WorkflowExecutionError as exc:
        original_exception = exc.original_exception
        audit_repository = WorkflowRunRepository(db=db)
        audit_repository.create_failed(
            workflow_id=exc.workflow_id,
            market_data_id=payload.market_data_id,
            started_at=datetime.fromisoformat(
                exc.workflow_started_at.replace("Z", "+00:00")
            ),
            completed_at=datetime.fromisoformat(
                exc.workflow_completed_at.replace("Z", "+00:00")
            ),
            workflow_latency_ms=exc.workflow_latency_ms,
            failed_agent=exc.failed_agent,
            error_type=type(original_exception).__name__,
            error_message=str(original_exception),
        )

        if isinstance(original_exception, MarketDataNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(original_exception),
            ) from original_exception

        raise original_exception
    except MarketDataNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    completed_at = state["workflow_completed_at"]
    if completed_at is None:
        raise RuntimeError("Completed workflow is missing workflow_completed_at")

    audit_repository = WorkflowRunRepository(db=db)
    audit_repository.create_success(
        workflow_id=state["workflow_id"],
        market_data_id=payload.market_data_id,
        started_at=datetime.fromisoformat(
            state["workflow_started_at"].replace("Z", "+00:00")
        ),
        completed_at=datetime.fromisoformat(
            completed_at.replace("Z", "+00:00")
        ),
        workflow_latency_ms=state.get("workflow_latency_ms"),
    )

    return MultiAgentAnalyzeResponse(
        workflow_id=state["workflow_id"],
        workflow_started_at=state["workflow_started_at"],
        workflow_completed_at=state["workflow_completed_at"] or "",
        market_analysis=state["market_analysis"] or {},
        risk_analysis=state["risk_analysis"] or {},
        decision=state["decision_analysis"] or {},
        explanation=state.get("explanation"),
        explanation_status=state.get("explanation_status"),
        explanation_model=state.get("explanation_model"),
        explanation_latency_ms=state.get("explanation_latency_ms"),
        explanation_error=state.get("explanation_error"),
        workflow_latency_ms=state.get("workflow_latency_ms"),
        agent_latency_ms=state.get("agent_latency_ms", {}),
        agent_status=state.get("agent_status", {}),
        visited_agents=state["visited_agents"],
        final_answer=state["final_answer"],
    )
