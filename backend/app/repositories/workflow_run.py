from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.workflow_run import WorkflowRun


class WorkflowRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_success(
        self,
        *,
        workflow_id: str,
        market_data_id: int,
        started_at: datetime,
        completed_at: datetime,
        workflow_latency_ms: float | None,
    ) -> WorkflowRun:
        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            market_data_id=market_data_id,
            started_at=started_at,
            completed_at=completed_at,
            workflow_latency_ms=workflow_latency_ms,
            status="success",
        )

        try:
            self.db.add(workflow_run)
            self.db.commit()
            self.db.refresh(workflow_run)
        except SQLAlchemyError:
            self.db.rollback()
            raise

        return workflow_run

    def create_failed(
        self,
        *,
        workflow_id: str,
        market_data_id: int,
        started_at: datetime,
        completed_at: datetime,
        workflow_latency_ms: float | None,
        failed_agent: str | None,
        error_type: str,
        error_message: str,
    ) -> WorkflowRun:
        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            market_data_id=market_data_id,
            started_at=started_at,
            completed_at=completed_at,
            workflow_latency_ms=workflow_latency_ms,
            status="failed",
            failed_agent=failed_agent,
            error_type=error_type,
            error_message=error_message,
        )

        try:
            self.db.add(workflow_run)
            self.db.commit()
            self.db.refresh(workflow_run)
        except SQLAlchemyError:
            self.db.rollback()
            raise

        return workflow_run
