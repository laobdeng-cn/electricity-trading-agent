from typing import Protocol

from app.schemas.analysis import MarketAnalysisResponse
from app.schemas.llm import LLMMarketInsight


class MarketInsightClient(Protocol):
    def generate_market_insight(
        self,
        analysis: MarketAnalysisResponse,
    ) -> LLMMarketInsight:
        ...
