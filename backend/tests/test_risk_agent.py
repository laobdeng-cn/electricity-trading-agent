from app.agents.risk_agent import RiskAgent


def test_risk_agent_marks_missing_forecast_as_high_risk() -> None:
    agent = RiskAgent()

    result = agent(
        {
            "market_data_id": 1,
            "price_gap_percent": None,
            "net_load_mw": 950.0,
            "renewable_ratio_percent": 26.92,
            "signal": "insufficient_data",
        }
    )

    assert result["risk_level"] == "high"
    assert result["risk_score"] == 50
    assert "missing_forecast_signal" in result["risk_factors"]
    assert "insufficient_market_signal_data" in result["risk_factors"]


def test_risk_agent_marks_stable_market_as_low_risk() -> None:
    agent = RiskAgent()

    result = agent(
        {
            "market_data_id": 3,
            "price_gap_percent": 0.5,
            "net_load_mw": 700.0,
            "renewable_ratio_percent": 30.0,
            "signal": "neutral",
        }
    )

    assert result["risk_level"] == "low"
    assert result["risk_score"] == 0
    assert result["risk_factors"] == []
    assert "未发现显著规则风险" in result["summary"]
