from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    market: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    node: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    load_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    renewable_mw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
