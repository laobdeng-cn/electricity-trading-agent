from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
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
