from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.dependencies import get_db
from app.main import app
from app.models.workflow_run import WorkflowRun


class FakeWorkflowRunDB:
    def __init__(
        self,
        workflow_run: WorkflowRun | None,
    ) -> None:
        self.workflow_run = workflow_run
        self.scalar_calls = 0

    def scalar(self, statement):
        self.scalar_calls += 1
        return self.workflow_run


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
