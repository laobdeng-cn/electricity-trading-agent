"""create workflow_runs table

Revision ID: a1b2c3d4e5f6
Revises: 7f2124c8bac6
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7f2124c8bac6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("market_data_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("workflow_latency_ms", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_workflow_runs_workflow_id"),
        "workflow_runs",
        ["workflow_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_workflow_runs_market_data_id"),
        "workflow_runs",
        ["market_data_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_runs_status"),
        "workflow_runs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_runs_status"), table_name="workflow_runs")
    op.drop_index(
        op.f("ix_workflow_runs_market_data_id"),
        table_name="workflow_runs",
    )
    op.drop_index(
        op.f("ix_workflow_runs_workflow_id"),
        table_name="workflow_runs",
    )
    op.drop_table("workflow_runs")
