from enum import Enum

from pydantic import BaseModel


class MarketSignal(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    INSUFFICIENT_DATA = "insufficient_data"


class MarketAnalysisResponse(BaseModel):
    market_data_id: int
    node: str
    price: float
    forecast_price: float | None
    price_gap: float | None
    price_gap_percent: float | None
    net_load_mw: float
    renewable_ratio_percent: float | None
    signal: MarketSignal
