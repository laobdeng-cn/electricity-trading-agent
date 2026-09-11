from app.llm.base import MarketInsightClient
from app.schemas.llm import LLMMarketAnalysisResponse
from app.services.analysis import MarketAnalysisService


class LLMMarketAnalysisService:
    def __init__(
        self,
        analysis_service: MarketAnalysisService,
        llm_client: MarketInsightClient,
    ) -> None:
        self.analysis_service = analysis_service
        self.llm_client = llm_client

    def analyze_market_data(
        self,
        market_data_id: int,
    ) -> LLMMarketAnalysisResponse | None:
        deterministic_analysis = self.analysis_service.analyze_market_data(
            market_data_id
        )

        if deterministic_analysis is None:
            return None

        insight = self.llm_client.generate_market_insight(
            deterministic_analysis
        )

        return LLMMarketAnalysisResponse(
            market_data_id=deterministic_analysis.market_data_id,
            node=deterministic_analysis.node,
            deterministic_signal=deterministic_analysis.signal,
            **insight.model_dump(),
        )
