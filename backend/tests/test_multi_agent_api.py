from fastapi.testclient import TestClient

from app.agents.market_analyst import MarketDataNotFoundError
from app.core.dependencies import get_multi_agent_runner
from app.main import app


class FakeMultiAgentRunner:
    def run(self, request: str):
        assert request == "分析市场数据 2"
        return {
            "request": request,
            "workflow_id": "test-workflow-id",
            "market_analysis": {
                "market_data_id": 2,
                "signal": "bullish",
                "price_gap_percent": 1.88,
            },
            "risk_analysis": {
                "risk_level": "medium",
                "risk_score": 18,
                "risk_factors": ["noticeable_price_gap:1.88%"],
                "summary": "风险等级 medium，评分 18/100。",
            },
            "decision_analysis": {
                "action": "cautious_buy",
                "market_signal": "bullish",
                "risk_level": "medium",
                "risk_score": 18,
                "summary": "决策动作 cautious_buy。",
            },
            "explanation": "市场偏多、风险中等，建议谨慎执行确定性决策。",
            "explanation_status": "llm",
            "explanation_model": "fake-explanation-model",
            "explanation_latency_ms": 12.5,
            "explanation_error": None,
            "final_answer": "市场偏多、风险中等，建议谨慎执行确定性决策。",
            "visited_agents": [
                "market_analyst",
                "risk",
                "decision",
                "explanation",
            ],
        }


class MissingMarketDataRunner:
    def run(self, request: str):
        raise MarketDataNotFoundError("Market data 999 not found")


def test_multi_agent_api_returns_structured_workflow_result() -> None:
    app.dependency_overrides[get_multi_agent_runner] = (
        lambda: FakeMultiAgentRunner()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/multi-agent/analyze",
                json={"market_data_id": 2},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["workflow_id"] == "test-workflow-id"
    assert body["market_analysis"]["signal"] == "bullish"
    assert body["risk_analysis"]["risk_score"] == 18
    assert body["decision"]["action"] == "cautious_buy"
    assert body["explanation_status"] == "llm"
    assert body["explanation_model"] == "fake-explanation-model"
    assert body["explanation_latency_ms"] == 12.5
    assert body["explanation_error"] is None
    assert body["visited_agents"] == [
        "market_analyst",
        "risk",
        "decision",
        "explanation",
    ]
    assert body["final_answer"] == (
        "市场偏多、风险中等，建议谨慎执行确定性决策。"
    )


def test_multi_agent_api_returns_404_when_market_data_is_missing() -> None:
    app.dependency_overrides[get_multi_agent_runner] = (
        lambda: MissingMarketDataRunner()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/multi-agent/analyze",
                json={"market_data_id": 999},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Market data 999 not found",
    }


def test_multi_agent_api_rejects_invalid_market_data_id() -> None:
    app.dependency_overrides[get_multi_agent_runner] = (
        lambda: FakeMultiAgentRunner()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/multi-agent/analyze",
                json={"market_data_id": 0},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
