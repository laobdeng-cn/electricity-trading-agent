from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MarketType(str, Enum):
    DAY_AHEAD = "day_ahead"
    REAL_TIME = "real_time"
    MID_LONG_TERM = "mid_long_term"
    AUXILIARY_SERVICE = "auxiliary_service"


class MarketDataCreate(BaseModel):
    market: MarketType

    node: str = Field(
        min_length=1,
        max_length=64,
        description="交易节点名称",
    )

    timestamp: datetime

    price: float = Field(
        gt=-10000,
        lt=100000,
        description="市场电价",
    )

    load_mw: float = Field(
        ge=0,
        description="系统负荷 MW",
    )

    renewable_mw: float = Field(
        ge=0,
        description="新能源出力 MW",
    )


class MarketDataResponse(MarketDataCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
