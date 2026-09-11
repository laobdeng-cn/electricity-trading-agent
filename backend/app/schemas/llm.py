from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.analysis import MarketSignal


class LLMMarketView(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    INSUFFICIENT_DATA = "insufficient_data"


class LLMMarketInsight(BaseModel):
    market_view: LLMMarketView
    confidence: float = Field(
        ge=0,
        le=1,
        description="模型自评置信度，仅用于辅助解释，不代表统计概率",
    )
    summary: str = Field(min_length=1, max_length=1000)
    key_drivers: list[str] = Field(default_factory=list, max_length=5)
    risk_factors: list[str] = Field(default_factory=list, max_length=5)


class LLMMarketAnalysisResponse(LLMMarketInsight):
    market_data_id: int
    node: str
    deterministic_signal: MarketSignal
