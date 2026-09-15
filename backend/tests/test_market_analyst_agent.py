import pytest

from app.agents.decision_agent import DecisionAgent
from app.agents.market_analyst import (
    MarketAnalystAgent,
    MarketDataNotFoundError,
)
from app.agents.risk_agent import RiskAgent
from app.graph.multi_agent_graph import MultiAgentGraphRunner
from app.schemas.analysis import MarketAnalysisResponse, MarketSignal


class FakeAnalysisService:
    def __init__(self, result: MarketAnalysisResponse | None) -> None:
        self.result = result
        self.requested_ids: list[int] = []

    def analyze_market_data(
        self,
        market_data_id: int,
    ) -> MarketAnalysisResponse | None:
        self.requested_ids.append(market_data_id)
        return self.result


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


def test_market_analyst_agent_uses_analysis_service() -> None:
    analysis_service = FakeAnalysisService(build_analysis())
    agent = MarketAnalystAgent(analysis_service)

    result = agent("分析市场数据 2")

    assert analysis_service.requested_ids == [2]
    assert result["market_data_id"] == 2
    assert result["node"] == "MAC_NODE_B"
    assert result["signal"] == "bullish"


def test_market_analyst_agent_raises_when_record_is_missing() -> None:
    analysis_service = FakeAnalysisService(None)
    agent = MarketAnalystAgent(analysis_service)

    with pytest.raises(
        MarketDataNotFoundError,
        match="Market data 999 not found",
    ):
        agent("分析市场数据 999")

    assert analysis_service.requested_ids == [999]


def test_multi_agent_graph_can_use_real_market_risk_and_decision_agents() -> None:
    analysis_service = FakeAnalysisService(build_analysis())
    market_analyst = MarketAnalystAgent(analysis_service)
    risk_agent = RiskAgent()
    decision_agent = DecisionAgent()

    runner = MultiAgentGraphRunner(
        market_analyst=market_analyst,
        risk_agent=risk_agent,
        decision_agent=decision_agent,
    )

    result = runner.run("分析市场数据 2")

    assert result["market_analysis"]["price_gap_percent"] == 1.88
    assert result["risk_analysis"]["risk_level"] == "medium"
    assert result["risk_analysis"]["risk_score"] == 18
    assert result["decision_analysis"]["action"] == "cautious_buy"
    assert result["visited_agents"] == [
        "market_analyst",
        "risk",
        "decision",
    ]
    assert "决策动作 cautious_buy" in result["final_answer"]
