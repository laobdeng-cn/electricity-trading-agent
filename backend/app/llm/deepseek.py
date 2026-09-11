import json

import httpx
from pydantic import ValidationError

from app.schemas.analysis import MarketAnalysisResponse
from app.schemas.llm import LLMMarketInsight


class LLMClientError(RuntimeError):
    pass


class LLMConfigurationError(LLMClientError):
    pass


class DeepSeekClient:
    SYSTEM_PROMPT = """
你是电力交易辅助决策系统中的市场分析助手。

你只负责基于系统已经计算好的结构化市场指标进行解释和风险提示，
不要重新计算或篡改输入数值，不要编造未提供的市场规则、天气、机组状态或政策信息。

请只输出合法 JSON，不要输出 Markdown、代码块或 JSON 之外的文字。
JSON 格式必须为：
{
  "market_view": "bullish | bearish | neutral | insufficient_data",
  "confidence": 0.0,
  "summary": "简洁的中文市场判断",
  "key_drivers": ["驱动因素1", "驱动因素2"],
  "risk_factors": ["风险因素1", "风险因素2"]
}

规则：
1. confidence 必须在 0 到 1 之间，它只是模型自评置信度，不是统计概率。
2. 如果 forecast_price 缺失，market_view 应优先使用 insufficient_data。
3. deterministic signal 是代码计算结果，应作为重要依据，但可以指出它的局限性。
4. key_drivers 和 risk_factors 最多各 5 条。
""".strip()

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_market_insight(
        self,
        analysis: MarketAnalysisResponse,
    ) -> LLMMarketInsight:
        if not self.api_key:
            raise LLMConfigurationError(
                "DeepSeek API key is not configured"
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "请根据下面的市场指标输出 JSON 分析：\n"
                        + json.dumps(
                            analysis.model_dump(mode="json"),
                            ensure_ascii=False,
                        )
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 900,
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMClientError(
                f"DeepSeek request failed: {exc}"
            ) from exc

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMClientError(
                "DeepSeek returned an unexpected response"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMClientError("DeepSeek returned empty content")

        try:
            return LLMMarketInsight.model_validate_json(content)
        except ValidationError as exc:
            raise LLMClientError(
                "DeepSeek JSON output did not match the expected schema"
            ) from exc
