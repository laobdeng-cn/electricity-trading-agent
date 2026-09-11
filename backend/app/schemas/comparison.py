from pydantic import BaseModel

from app.schemas.analysis import MarketSignal


class MarketComparisonResponse(BaseModel):
    first_market_data_id: int
    second_market_data_id: int
    first_node: str
    second_node: str
    price_delta: float
    forecast_price_delta: float | None
    net_load_delta_mw: float
    renewable_ratio_delta_percent: float | None
    first_signal: MarketSignal
    second_signal: MarketSignal
