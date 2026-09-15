from typing import Any

from app.agents.explanation_agent import ExplanationAgent
from app.graph.multi_agent_graph import MultiAgentGraphRunner


class FakeExplanationProvider:
    def generate_explanation(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        assert market_analysis["signal"] == "bullish"
        assert risk_analysis["risk_score"] == 18
        assert decision_analysis["action"] == "cautious_buy"

        # Mutate the provider-side copies deliberately. The deterministic
        # workflow state must remain unchanged.
        risk_analysis["risk_score"] = 999
        decision_analysis["action"] = "override_attempt"

        return "市场偏多、风险中等，系统确定性决策为谨慎买入。"


def test_explanation_agent_cannot_mutate_deterministic_inputs() -> None:
    market_analysis = {"signal": "bullish"}
    risk_analysis = {"risk_level": "medium", "risk_score": 18}
    decision_analysis = {"action": "cautious_buy"}

    agent = ExplanationAgent(FakeExplanationProvider())
    explanation = agent(
        market_analysis,
        risk_analysis,
        decision_analysis,
    )

    assert explanation == "市场偏多、风险中等，系统确定性决策为谨慎买入。"
    assert risk_analysis["risk_score"] == 18
    assert decision_analysis["action"] == "cautious_buy"


def test_multi_agent_graph_can_finish_with_explanation_agent() -> None:
    explanation_agent = ExplanationAgent(FakeExplanationProvider())

    runner = MultiAgentGraphRunner(
        market_analyst=lambda request: {
            "market_data_id": 2,
            "signal": "bullish",
        },
        risk_agent=lambda market: {
            "risk_level": "medium",
            "risk_score": 18,
        },
        decision_agent=lambda market, risk: {
            "action": "cautious_buy",
            "summary": "决策动作 cautious_buy。",
        },
        explanation_agent=explanation_agent,
    )

    result = runner.run("分析市场数据 2")

    assert result["risk_analysis"]["risk_score"] == 18
    assert result["decision_analysis"]["action"] == "cautious_buy"
    assert result["explanation"] == (
        "市场偏多、风险中等，系统确定性决策为谨慎买入。"
    )
    assert result["final_answer"] == result["explanation"]
    assert result["visited_agents"] == [
        "market_analyst",
        "risk",
        "decision",
        "explanation",
    ]
