from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.workflow_run import WorkflowRun
from app.repositories.workflow_run import WorkflowRunRepository
from app.schemas.workflow_run import WorkflowRunResponse


router = APIRouter(
    prefix="/workflow-runs",
    tags=["Workflow Audit"],
)


@router.get(
    "",
    response_model=list[WorkflowRunResponse],
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
) -> list[WorkflowRun]:
    repository = WorkflowRunRepository(db=db)
    return repository.list_recent(
        limit=limit,
        offset=offset,
        status=status_filter,
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
