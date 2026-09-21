from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.dependencies import get_db
from app.main import app
from app.models.workflow_run import WorkflowRun


class FakeExecuteResult:
    def __init__(
        self,
        row: tuple[int, int, int, float | None],
    ) -> None:
        self.row = row

    def one(self) -> tuple[int, int, int, float | None]:
        return self.row


class FakeScalarResult:
    def __init__(
        self,
        items: list[WorkflowRun],
    ) -> None:
        self.items = items

    def all(self) -> list[WorkflowRun]:
        return self.items


class FakeWorkflowRunDB:
    def __init__(
        self,
        workflow_run: WorkflowRun | None = None,
        workflow_runs: list[WorkflowRun] | None = None,
        total: int | None = None,
        stats: tuple[int, int, int, float | None] | None = None,
    ) -> None:
        self.workflow_run = workflow_run
        self.workflow_runs = workflow_runs or []
        self.total = (
            len(self.workflow_runs)
            if total is None
            else total
        )
        self.scalar_calls = 0
        self.scalars_calls = 0
        self.last_scalars_statement = None
        self.last_count_statement = None
        self.stats = stats or (0, 0, 0, None)
        self.execute_calls = 0
        self.last_execute_statement = None

    def scalar(self, statement):
        self.scalar_calls += 1
        if "count(" in str(statement).lower():
            self.last_count_statement = statement
            return self.total
        return self.workflow_run

    def scalars(self, statement):
        self.scalars_calls += 1
        self.last_scalars_statement = statement
        return FakeScalarResult(self.workflow_runs)

    def execute(self, statement):
        self.execute_calls += 1
        self.last_execute_statement = statement
        return FakeExecuteResult(self.stats)


def test_workflow_run_api_returns_audit_record() -> None:
    workflow_run = WorkflowRun(
        id=2,
        workflow_id="07b0d4a8-f44d-4709-991f-a02df8d0517d",
        market_data_id=999,
        started_at=datetime(
            2026,
            9,
            21,
            15,
            40,
            46,
            593061,
            tzinfo=timezone.utc,
        ),
        completed_at=datetime(
            2026,
            9,
            21,
            15,
            40,
            46,
            650600,
            tzinfo=timezone.utc,
        ),
        workflow_latency_ms=57.534,
        status="failed",
        failed_agent="market_analyst",
        error_type="MarketDataNotFoundError",
        error_message="Market data 999 not found",
        created_at=datetime(
            2026,
            9,
            21,
            15,
            40,
            46,
            651000,
            tzinfo=timezone.utc,
        ),
    )
    db = FakeWorkflowRunDB(workflow_run)
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs/"
                "07b0d4a8-f44d-4709-991f-a02df8d0517d"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 2
    assert body["workflow_id"] == (
        "07b0d4a8-f44d-4709-991f-a02df8d0517d"
    )
    assert body["market_data_id"] == 999
    assert body["status"] == "failed"
    assert body["failed_agent"] == "market_analyst"
    assert body["error_type"] == "MarketDataNotFoundError"
    assert body["error_message"] == "Market data 999 not found"
    assert body["workflow_latency_ms"] == 57.534
    assert db.scalar_calls == 1


def test_workflow_run_api_returns_404_when_missing() -> None:
    db = FakeWorkflowRunDB(None)
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs/missing-workflow-id"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Workflow run missing-workflow-id not found",
    }
    assert db.scalar_calls == 1


def _build_workflow_run(
    *,
    row_id: int,
    workflow_id: str,
    market_data_id: int,
    status_value: str,
) -> WorkflowRun:
    return WorkflowRun(
        id=row_id,
        workflow_id=workflow_id,
        market_data_id=market_data_id,
        started_at=datetime(
            2026,
            9,
            21,
            15,
            40,
            46,
            tzinfo=timezone.utc,
        ),
        completed_at=datetime(
            2026,
            9,
            21,
            15,
            40,
            47,
            tzinfo=timezone.utc,
        ),
        workflow_latency_ms=1000.0,
        status=status_value,
        failed_agent=(
            "market_analyst"
            if status_value == "failed"
            else None
        ),
        error_type=(
            "RuntimeError"
            if status_value == "failed"
            else None
        ),
        error_message=(
            "failed"
            if status_value == "failed"
            else None
        ),
        created_at=datetime(
            2026,
            9,
            21,
            15,
            40,
            47,
            tzinfo=timezone.utc,
        ),
    )


def test_workflow_run_api_lists_recent_records() -> None:
    runs = [
        _build_workflow_run(
            row_id=2,
            workflow_id="failed-run",
            market_data_id=999,
            status_value="failed",
        ),
        _build_workflow_run(
            row_id=1,
            workflow_id="success-run",
            market_data_id=2,
            status_value="success",
        ),
    ]
    db = FakeWorkflowRunDB(
        workflow_runs=runs,
        total=2,
    )
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get("/api/workflow-runs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert [item["workflow_id"] for item in body["items"]] == [
        "failed-run",
        "success-run",
    ]
    assert body["total"] == 2
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert db.scalars_calls == 1
    assert db.scalar_calls == 1

    statement = str(db.last_scalars_statement)
    assert "ORDER BY workflow_runs.created_at DESC" in statement
    assert "workflow_runs.id DESC" in statement
    assert "LIMIT" in statement
    assert "OFFSET" in statement


def test_workflow_run_api_filters_by_status() -> None:
    runs = [
        _build_workflow_run(
            row_id=2,
            workflow_id="failed-run",
            market_data_id=999,
            status_value="failed",
        ),
    ]
    db = FakeWorkflowRunDB(
        workflow_runs=runs,
        total=7,
    )
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs?status=failed&limit=10&offset=3"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["status"] == "failed"
    assert body["total"] == 7
    assert body["limit"] == 10
    assert body["offset"] == 3
    assert db.scalars_calls == 1
    assert db.scalar_calls == 1

    statement = str(db.last_scalars_statement)
    assert "workflow_runs.status =" in statement

    count_statement = str(db.last_count_statement)
    assert "workflow_runs.status =" in count_statement
    assert "LIMIT" not in count_statement
    assert "OFFSET" not in count_statement


def test_workflow_run_api_rejects_invalid_status() -> None:
    db = FakeWorkflowRunDB()
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs?status=running"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert db.scalars_calls == 0


def test_workflow_run_api_filters_by_market_data_id() -> None:
    runs = [
        _build_workflow_run(
            row_id=1,
            workflow_id="success-run",
            market_data_id=2,
            status_value="success",
        ),
    ]
    db = FakeWorkflowRunDB(workflow_runs=runs)
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs?market_data_id=2"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["market_data_id"] == 2
    assert body["total"] == 1
    assert db.scalars_calls == 1
    assert db.scalar_calls == 1

    statement = str(db.last_scalars_statement)
    assert "workflow_runs.market_data_id =" in statement


def test_workflow_run_api_filters_by_started_time_range() -> None:
    runs = [
        _build_workflow_run(
            row_id=1,
            workflow_id="success-run",
            market_data_id=2,
            status_value="success",
        ),
    ]
    db = FakeWorkflowRunDB(workflow_runs=runs)
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs"
                "?started_from=2026-09-21T15:00:00Z"
                "&started_to=2026-09-21T16:00:00Z"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert db.scalars_calls == 1
    assert db.scalar_calls == 1

    statement = str(db.last_scalars_statement)
    assert "workflow_runs.started_at >=" in statement
    assert "workflow_runs.started_at <=" in statement


def test_workflow_run_api_rejects_invalid_started_time_range() -> None:
    db = FakeWorkflowRunDB()
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs"
                "?started_from=2026-09-21T17:00:00Z"
                "&started_to=2026-09-21T16:00:00Z"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "started_from must be less than or equal to started_to"
        ),
    }
    assert db.scalars_calls == 0



def test_workflow_run_stats_api_returns_aggregates() -> None:
    db = FakeWorkflowRunDB(
        stats=(2, 1, 1, 1334.385),
    )
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get("/api/workflow-runs/stats")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "total": 2,
        "success": 1,
        "failed": 1,
        "average_latency_ms": 1334.385,
    }
    assert db.execute_calls == 1


def test_workflow_run_stats_api_applies_filters() -> None:
    db = FakeWorkflowRunDB(
        stats=(1, 0, 1, 57.534),
    )
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs/stats"
                "?status=failed"
                "&market_data_id=999"
                "&started_from=2026-09-21T15:00:00Z"
                "&started_to=2026-09-21T16:00:00Z"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "total": 1,
        "success": 0,
        "failed": 1,
        "average_latency_ms": 57.534,
    }

    statement = str(db.last_execute_statement)
    assert "workflow_runs.status =" in statement
    assert "workflow_runs.market_data_id =" in statement
    assert "workflow_runs.started_at >=" in statement
    assert "workflow_runs.started_at <=" in statement
    assert "LIMIT" not in statement
    assert "OFFSET" not in statement


def test_workflow_run_stats_api_handles_empty_result() -> None:
    db = FakeWorkflowRunDB(
        stats=(0, 0, 0, None),
    )
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs/stats?market_data_id=123456"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "success": 0,
        "failed": 0,
        "average_latency_ms": None,
    }
    assert db.execute_calls == 1
