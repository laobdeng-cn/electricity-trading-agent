"""create market_data table

Revision ID: 0001_create_market_data
Revises:
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_create_market_data"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("node", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("load_mw", sa.Float(), nullable=False),
        sa.Column("renewable_mw", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_market_data_market"),
        "market_data",
        ["market"],
        unique=False,
    )
    op.create_index(
        op.f("ix_market_data_node"),
        "market_data",
        ["node"],
        unique=False,
    )
    op.create_index(
        op.f("ix_market_data_timestamp"),
        "market_data",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_market_data_timestamp"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_node"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_market"), table_name="market_data")
    op.drop_table("market_data")
