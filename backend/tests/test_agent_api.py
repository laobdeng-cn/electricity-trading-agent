from fastapi.testclient import TestClient

from app.core.dependencies import get_market_agent_service
from app.llm.deepseek import LLMClientError
from app.main import app


class FailingMarketAgentService:
    def chat(self, message: str):
        raise LLMClientError("agent execution failed")


def test_agent_api_returns_502_for_llm_client_error() -> None:
    app.dependency_overrides[get_market_agent_service] = (
        lambda: FailingMarketAgentService()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/agent/chat",
                json={"message": "分析市场数据 2"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {
        "detail": "agent execution failed",
    }
