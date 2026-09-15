import json
from typing import Any

import pytest

from app.llm.deepseek import LLMConfigurationError
from app.llm.deepseek_explanation import DeepSeekExplanationProvider


class FakeResponse:
    def __init__(self, explanation: str) -> None:
        self.explanation = explanation

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"explanation": self.explanation},
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }


def test_deepseek_explanation_provider_requires_api_key() -> None:
    provider = DeepSeekExplanationProvider(
        api_key=None,
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
    )

    with pytest.raises(
        LLMConfigurationError,
        match="API key is not configured",
    ):
        provider.generate_explanation(
            {"signal": "bullish"},
            {"risk_level": "medium", "risk_score": 18},
            {"action": "cautious_buy"},
        )


def test_deepseek_explanation_provider_sends_deterministic_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> FakeResponse:
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse("市场偏多、风险中等，维持谨慎买入观察。")

    monkeypatch.setattr(
        "app.llm.deepseek_explanation.httpx.post",
        fake_post,
    )

    market_analysis = {
        "market_data_id": 2,
        "signal": "bullish",
        "price_gap_percent": 1.88,
    }
    risk_analysis = {
        "risk_level": "medium",
        "risk_score": 18,
    }
    decision_analysis = {
        "action": "cautious_buy",
    }
    provider = DeepSeekExplanationProvider(
        api_key="test-key",
        base_url="https://api.deepseek.com/",
        model="deepseek-v4-flash",
        timeout_seconds=12.0,
    )

    result = provider.generate_explanation(
        market_analysis,
        risk_analysis,
        decision_analysis,
    )

    assert result == "市场偏多、风险中等，维持谨慎买入观察。"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["timeout"] == 12.0
    payload = captured["json"]
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["response_format"] == {"type": "json_object"}
    user_content = payload["messages"][1]["content"]
    assert '"risk_score": 18' in user_content
    assert '"action": "cautious_buy"' in user_content
    assert "不得重新计算、修改或覆盖任何输入字段" in payload["messages"][0]["content"]
