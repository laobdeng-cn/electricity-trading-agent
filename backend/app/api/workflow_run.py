from datetime import datetime

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.workflow_run import WorkflowRun
from app.repositories.workflow_run import WorkflowRunRepository
from app.schemas.workflow_run import (
    WorkflowRunPageResponse,
    WorkflowRunResponse,
    WorkflowRunStatsResponse,
)


router = APIRouter(
    prefix="/workflow-runs",
    tags=["Workflow Audit"],
)


@router.get(
    "",
    response_model=WorkflowRunPageResponse,
)
def list_workflow_runs(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    status_filter: Annotated[
        Literal["success", "failed"] | None,
        Query(alias="status"),
    ] = None,
    market_data_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    started_from: Annotated[
        datetime | None,
        Query(),
    ] = None,
    started_to: Annotated[
        datetime | None,
        Query(),
    ] = None,
) -> WorkflowRunPageResponse:
    if (
        started_from is not None
        and started_to is not None
        and started_from > started_to
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "started_from must be less than or equal to started_to"
            ),
        )

    repository = WorkflowRunRepository(db=db)
    items = repository.list_recent(
        limit=limit,
        offset=offset,
        status=status_filter,
        market_data_id=market_data_id,
        started_from=started_from,
        started_to=started_to,
    )
    total = repository.count_recent(
        status=status_filter,
        market_data_id=market_data_id,
        started_from=started_from,
        started_to=started_to,
    )

    return WorkflowRunPageResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stats",
    response_model=WorkflowRunStatsResponse,
)
def get_workflow_run_stats(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    status_filter: Annotated[
        Literal["success", "failed"] | None,
        Query(alias="status"),
    ] = None,
    market_data_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    started_from: Annotated[
        datetime | None,
        Query(),
    ] = None,
    started_to: Annotated[
        datetime | None,
        Query(),
    ] = None,
) -> WorkflowRunStatsResponse:
    if (
        started_from is not None
        and started_to is not None
        and started_from > started_to
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "started_from must be less than or equal to started_to"
            ),
        )

    repository = WorkflowRunRepository(db=db)
    total, success_count, failed_count, average_latency_ms = (
        repository.get_stats(
            status=status_filter,
            market_data_id=market_data_id,
            started_from=started_from,
            started_to=started_to,
        )
    )

    return WorkflowRunStatsResponse(
        total=total,
        success=success_count,
        failed=failed_count,
        average_latency_ms=average_latency_ms,
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowRunResponse,
)
def get_workflow_run(
    workflow_id: str,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> WorkflowRun:
    repository = WorkflowRunRepository(db=db)
    workflow_run = repository.get_by_workflow_id(workflow_id)

    if workflow_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run {workflow_id} not found",
        )

    return workflow_run
