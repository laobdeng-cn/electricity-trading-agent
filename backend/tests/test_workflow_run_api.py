from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.dependencies import get_db
from app.main import app
from app.models.workflow_run import WorkflowRun


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
    ) -> None:
        self.workflow_run = workflow_run
        self.workflow_runs = workflow_runs or []
        self.scalar_calls = 0
        self.scalars_calls = 0
        self.last_scalars_statement = None

    def scalar(self, statement):
        self.scalar_calls += 1
        return self.workflow_run

    def scalars(self, statement):
        self.scalars_calls += 1
        self.last_scalars_statement = statement
        return FakeScalarResult(self.workflow_runs)


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
    db = FakeWorkflowRunDB(workflow_runs=runs)
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get("/api/workflow-runs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert [item["workflow_id"] for item in body] == [
        "failed-run",
        "success-run",
    ]
    assert db.scalars_calls == 1

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
    db = FakeWorkflowRunDB(workflow_runs=runs)
    app.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/workflow-runs?status=failed&limit=10&offset=0"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["status"] == "failed"
    assert db.scalars_calls == 1

    statement = str(db.last_scalars_statement)
    assert "workflow_runs.status =" in statement


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
