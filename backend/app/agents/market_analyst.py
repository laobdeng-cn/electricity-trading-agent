import re
from typing import Protocol

from app.schemas.analysis import MarketAnalysisResponse


class MarketDataNotFoundError(RuntimeError):
    """Raised when a requested market data record does not exist."""


class MarketAnalysisProvider(Protocol):
    def analyze_market_data(
        self,
        market_data_id: int,
    ) -> MarketAnalysisResponse | None:
        ...


class MarketAnalystAgent:
    """Adapter that exposes MarketAnalysisService as a multi-agent node."""

    def __init__(self, analysis_service: MarketAnalysisProvider) -> None:
        self.analysis_service = analysis_service

    def __call__(self, request: str) -> dict:
        market_data_id = self._extract_market_data_id(request)
        analysis = self.analysis_service.analyze_market_data(market_data_id)

        if analysis is None:
            raise MarketDataNotFoundError(
                f"Market data {market_data_id} not found"
            )

        return analysis.model_dump(mode="json")

    @staticmethod
    def _extract_market_data_id(request: str) -> int:
        match = re.search(r"\d+", request)
        if match is None:
            raise ValueError("market_data_id is required")
        return int(match.group())
