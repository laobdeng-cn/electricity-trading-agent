from copy import deepcopy
from typing import Any, Protocol

from app.llm.deepseek import LLMClientError


class ExplanationProvider(Protocol):
    def generate_explanation(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        ...


class ExplanationAgent:
    """Generate a human-readable report without changing deterministic outputs."""

    def __init__(self, provider: ExplanationProvider) -> None:
        self.provider = provider

    def __call__(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        explanation = self.provider.generate_explanation(
            deepcopy(market_analysis),
            deepcopy(risk_analysis),
            deepcopy(decision_analysis),
        )

        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("Explanation provider returned empty content")

        return explanation.strip()


class ResilientExplanationAgent:
    """Keep deterministic decisions available when the LLM explanation fails."""

    def __init__(self, agent: ExplanationAgent) -> None:
        self.agent = agent

    def __call__(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        try:
            return self.agent(
                market_analysis,
                risk_analysis,
                decision_analysis,
            )
        except LLMClientError:
            summary = decision_analysis.get("summary")
            if isinstance(summary, str) and summary.strip():
                return (
                    "AI解释暂不可用；以下为确定性决策摘要："
                    f"{summary.strip()}"
                )

            return (
                "AI解释暂不可用；请以结构化市场分析、风险评估和"
                "确定性决策字段为准。"
            )
