from typing import Any

import pytest

from app.graph.multi_agent_graph import MultiAgentGraphRunner


def test_multi_agent_graph_runs_market_then_risk() -> None:
    call_order: list[str] = []

    def market_analyst(request: str) -> dict[str, Any]:
        call_order.append("market_analyst")
        assert request == "分析市场数据 2"
        return {
            "market_data_id": 2,
            "signal": "bullish",
            "price_gap_percent": 1.88,
        }

    def risk_agent(
        market_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        call_order.append("risk")
        assert market_analysis["signal"] == "bullish"
        assert market_analysis["market_data_id"] == 2
        return {
            "risk_level": "medium",
            "summary": "市场偏多，但仍需控制价格预测偏差风险。",
        }

    runner = MultiAgentGraphRunner(
        market_analyst=market_analyst,
        risk_agent=risk_agent,
    )

    state = runner.run("分析市场数据 2")

    assert call_order == ["market_analyst", "risk"]
    assert state["market_analysis"]["signal"] == "bullish"
    assert state["risk_analysis"]["risk_level"] == "medium"
    assert state["final_answer"] == "市场偏多，但仍需控制价格预测偏差风险。"
    assert state["visited_agents"] == ["market_analyst", "risk"]


def test_multi_agent_graph_requires_market_analysis_before_risk() -> None:
    runner = MultiAgentGraphRunner(
        market_analyst=lambda request: None,  # type: ignore[arg-type, return-value]
        risk_agent=lambda analysis: {"summary": "unexpected"},
    )

    with pytest.raises(
        RuntimeError,
        match="Risk agent requires market analysis",
    ):
        runner.run("分析市场数据 2")
