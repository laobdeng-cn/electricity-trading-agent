from app.db.base import Base
from app.models.workflow_run import WorkflowRun


def test_workflow_run_model_registers_expected_table() -> None:
    table = WorkflowRun.__table__

    assert table is Base.metadata.tables["workflow_runs"]
    assert {
        "id",
        "workflow_id",
        "market_data_id",
        "started_at",
        "completed_at",
        "workflow_latency_ms",
        "status",
        "created_at",
    } == set(table.columns.keys())

    assert table.c.workflow_id.unique is True
    assert table.c.workflow_id.index is True
    assert table.c.market_data_id.index is True
    assert table.c.status.index is True
    assert table.c.completed_at.nullable is True
    assert table.c.workflow_latency_ms.nullable is True
