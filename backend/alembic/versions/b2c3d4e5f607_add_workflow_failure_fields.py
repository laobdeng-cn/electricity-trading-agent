"""add workflow failure audit fields

Revision ID: b2c3d4e5f607
Revises: a1b2c3d4e5f6
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f607"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column("failed_agent", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("error_type", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_runs", "error_message")
    op.drop_column("workflow_runs", "error_type")
    op.drop_column("workflow_runs", "failed_agent")
