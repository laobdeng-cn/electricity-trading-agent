from app.agents.decision_agent import DecisionAgent


def test_decision_agent_returns_cautious_buy_for_bullish_medium_risk() -> None:
    agent = DecisionAgent()

    result = agent(
        {"signal": "bullish"},
        {"risk_level": "medium", "risk_score": 18},
    )

    assert result["action"] == "cautious_buy"
    assert result["market_signal"] == "bullish"
    assert result["risk_level"] == "medium"
    assert result["risk_score"] == 18


def test_decision_agent_avoids_high_risk_even_when_signal_is_bullish() -> None:
    agent = DecisionAgent()

    result = agent(
        {"signal": "bullish"},
        {"risk_level": "high", "risk_score": 60},
    )

    assert result["action"] == "avoid"
    assert result["risk_level"] == "high"
    assert "优先规避交易暴露" in result["reason"]
