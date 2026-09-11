import pytest

from app.llm.deepseek import DeepSeekClient, LLMConfigurationError
from app.schemas.analysis import MarketAnalysisResponse, MarketSignal
from app.schemas.llm import LLMMarketInsight, LLMMarketView
from app.services.llm_analysis import LLMMarketAnalysisService


class FakeAnalysisService:
    def __init__(
        self,
        analysis: MarketAnalysisResponse | None,
    ) -> None:
        self.analysis = analysis

    def analyze_market_data(
        self,
        market_data_id: int,
    ) -> MarketAnalysisResponse | None:
        return self.analysis


class FakeLLMClient:
    def __init__(self, insight: LLMMarketInsight) -> None:
        self.insight = insight
        self.called_with: MarketAnalysisResponse | None = None

    def generate_market_insight(
        self,
        analysis: MarketAnalysisResponse,
    ) -> LLMMarketInsight:
        self.called_with = analysis
        return self.insight


def build_analysis() -> MarketAnalysisResponse:
    return MarketAnalysisResponse(
        market_data_id=2,
        node="MAC_NODE_B",
        price=405.2,
        forecast_price=412.8,
        price_gap=7.6,
        price_gap_percent=1.88,
        net_load_mw=1120.0,
        renewable_ratio_percent=21.13,
        signal=MarketSignal.BULLISH,
    )


def test_llm_analysis_combines_deterministic_and_llm_results() -> None:
    deterministic = build_analysis()
    insight = LLMMarketInsight(
        market_view=LLMMarketView.BULLISH,
        confidence=0.82,
        summary="预测电价高于当前价格，短期价格存在上行倾向。",
        key_drivers=["预测价格偏高", "净负荷较高"],
        risk_factors=["仅有单点预测数据"],
    )
    llm_client = FakeLLMClient(insight)
    service = LLMMarketAnalysisService(
        analysis_service=FakeAnalysisService(deterministic),
        llm_client=llm_client,
    )

    result = service.analyze_market_data(2)

    assert result is not None
    assert result.market_data_id == 2
    assert result.node == "MAC_NODE_B"
    assert result.deterministic_signal == MarketSignal.BULLISH
    assert result.market_view == LLMMarketView.BULLISH
    assert result.confidence == 0.82
    assert llm_client.called_with == deterministic


def test_llm_analysis_skips_llm_when_market_data_is_missing() -> None:
    insight = LLMMarketInsight(
        market_view=LLMMarketView.NEUTRAL,
        confidence=0.5,
        summary="unused",
        key_drivers=[],
        risk_factors=[],
    )
    llm_client = FakeLLMClient(insight)
    service = LLMMarketAnalysisService(
        analysis_service=FakeAnalysisService(None),
        llm_client=llm_client,
    )

    result = service.analyze_market_data(999)

    assert result is None
    assert llm_client.called_with is None


def test_deepseek_client_requires_api_key() -> None:
    client = DeepSeekClient(
        api_key=None,
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
    )

    with pytest.raises(LLMConfigurationError):
        client.generate_market_insight(build_analysis())
