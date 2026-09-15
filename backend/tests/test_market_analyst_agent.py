from app.agents.market_analyst import MarketAnalystAgent
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


def test_multi_agent_graph_can_use_real_market_and_risk_agents() -> None:
    analysis_service = FakeAnalysisService(build_analysis())
    market_analyst = MarketAnalystAgent(analysis_service)
    risk_agent = RiskAgent()

    runner = MultiAgentGraphRunner(
        market_analyst=market_analyst,
        risk_agent=risk_agent,
    )

    result = runner.run("分析市场数据 2")

    assert result["market_analysis"]["price_gap_percent"] == 1.88
    assert result["risk_analysis"]["risk_level"] == "medium"
    assert result["risk_analysis"]["risk_score"] == 18
    assert result["visited_agents"] == ["market_analyst", "risk"]
    assert "风险等级 medium" in result["final_answer"]
