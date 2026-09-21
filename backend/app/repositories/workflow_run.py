from datetime import datetime

from sqlalchemy import case, func, select
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

    def get_by_workflow_id(
        self,
        workflow_id: str,
    ) -> WorkflowRun | None:
        statement = select(WorkflowRun).where(
            WorkflowRun.workflow_id == workflow_id
        )
        return self.db.scalar(statement)

    @staticmethod
    def _apply_filters(
        statement,
        *,
        status: str | None = None,
        market_data_id: int | None = None,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
    ):
        if status is not None:
            statement = statement.where(
                WorkflowRun.status == status
            )

        if market_data_id is not None:
            statement = statement.where(
                WorkflowRun.market_data_id == market_data_id
            )

        if started_from is not None:
            statement = statement.where(
                WorkflowRun.started_at >= started_from
            )

        if started_to is not None:
            statement = statement.where(
                WorkflowRun.started_at <= started_to
            )

        return statement

    def list_recent(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        market_data_id: int | None = None,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
    ) -> list[WorkflowRun]:
        statement = self._apply_filters(
            select(WorkflowRun),
            status=status,
            market_data_id=market_data_id,
            started_from=started_from,
            started_to=started_to,
        )

        statement = (
            statement
            .order_by(
                WorkflowRun.created_at.desc(),
                WorkflowRun.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(statement).all())

    def count_recent(
        self,
        *,
        status: str | None = None,
        market_data_id: int | None = None,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
    ) -> int:
        statement = self._apply_filters(
            select(func.count()).select_from(WorkflowRun),
            status=status,
            market_data_id=market_data_id,
            started_from=started_from,
            started_to=started_to,
        )
        total = self.db.scalar(statement)
        return int(total or 0)


    def get_stats(
        self,
        *,
        status: str | None = None,
        market_data_id: int | None = None,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
    ) -> tuple[int, int, int, float | None]:
        statement = self._apply_filters(
            select(
                func.count(WorkflowRun.id),
                func.coalesce(
                    func.sum(
                        case(
                            (WorkflowRun.status == "success", 1),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (WorkflowRun.status == "failed", 1),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.avg(WorkflowRun.workflow_latency_ms),
            ).select_from(WorkflowRun),
            status=status,
            market_data_id=market_data_id,
            started_from=started_from,
            started_to=started_to,
        )

        row = self.db.execute(statement).one()
        average_latency_ms = (
            float(row[3])
            if row[3] is not None
            else None
        )

        return (
            int(row[0] or 0),
            int(row[1] or 0),
            int(row[2] or 0),
            average_latency_ms,
        )


