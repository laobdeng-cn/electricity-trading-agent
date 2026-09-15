import json
from typing import Any

import httpx

from app.llm.deepseek import LLMClientError, LLMConfigurationError


class DeepSeekExplanationProvider:
    """Generate a trader-facing explanation from deterministic agent outputs."""

    SYSTEM_PROMPT = """
你是电力交易辅助决策系统中的解释 Agent。

系统已经完成市场分析、风险评估和确定性决策。你只负责把这些结果整理成交易员可读的中文说明。

硬性约束：
1. 不得重新计算、修改或覆盖任何输入字段。
2. risk_score、risk_level、action 都是上游确定性模块的最终结果，不得提出替代值。
3. 不得编造天气、机组状态、市场规则、政策、交易结果或未提供的数据。
4. 可以解释数据局限和风险来源，但不能把确定性规则包装成收益承诺。
5. 只输出合法 JSON，不要输出 Markdown、代码块或额外文字。

输出格式：
{
  "explanation": "面向交易员的简洁中文说明"
}
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

    def generate_explanation(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        if not self.api_key:
            raise LLMConfigurationError(
                "DeepSeek API key is not configured"
            )

        deterministic_result = {
            "market_analysis": market_analysis,
            "risk_analysis": risk_analysis,
            "decision_analysis": decision_analysis,
        }
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
                        "请解释下面的确定性多 Agent 结果：\n"
                        + json.dumps(
                            deterministic_result,
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
                f"DeepSeek explanation request failed: {exc}"
            ) from exc

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMClientError(
                "DeepSeek returned an unexpected explanation response"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMClientError(
                "DeepSeek returned empty explanation content"
            )

        try:
            parsed = json.loads(content)
            explanation = parsed["explanation"]
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise LLMClientError(
                "DeepSeek explanation output did not match the expected schema"
            ) from exc

        if not isinstance(explanation, str) or not explanation.strip():
            raise LLMClientError(
                "DeepSeek returned empty explanation"
            )

        return explanation.strip()
