from copy import deepcopy
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal, Protocol

from app.llm.deepseek import LLMClientError


class ExplanationProvider(Protocol):
    def generate_explanation(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        ...


@dataclass(frozen=True)
class ExplanationObservation:
    explanation: str
    status: Literal["llm", "fallback"]
    model: str | None
    latency_ms: float
    error: str | None = None


class ExplanationAgent:
    """Generate a human-readable report without changing deterministic outputs."""

    def __init__(self, provider: ExplanationProvider) -> None:
        self.provider = provider
        model = getattr(provider, "model", None)
        self.model_name = (
            model.strip()
            if isinstance(model, str) and model.strip()
            else None
        )

    def _generate_text(
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

    def __call__(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        return self._generate_text(
            market_analysis,
            risk_analysis,
            decision_analysis,
        )

    def generate_observation(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> ExplanationObservation:
        started_at = perf_counter()
        explanation = self._generate_text(
            market_analysis,
            risk_analysis,
            decision_analysis,
        )
        latency_ms = (perf_counter() - started_at) * 1000

        return ExplanationObservation(
            explanation=explanation,
            status="llm",
            model=self.model_name,
            latency_ms=round(latency_ms, 3),
        )


class ResilientExplanationAgent:
    """Keep deterministic decisions available when the LLM explanation fails."""

    def __init__(self, agent: ExplanationAgent) -> None:
        self.agent = agent

    def _fallback_text(
        self,
        decision_analysis: dict[str, Any],
    ) -> str:
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

    def __call__(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> str:
        return self.generate_observation(
            market_analysis,
            risk_analysis,
            decision_analysis,
        ).explanation

    def generate_observation(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
        decision_analysis: dict[str, Any],
    ) -> ExplanationObservation:
        started_at = perf_counter()
        try:
            return self.agent.generate_observation(
                market_analysis,
                risk_analysis,
                decision_analysis,
            )
        except LLMClientError as exc:
            latency_ms = (perf_counter() - started_at) * 1000
            error = str(exc).strip() or exc.__class__.__name__

            return ExplanationObservation(
                explanation=self._fallback_text(decision_analysis),
                status="fallback",
                model=self.agent.model_name,
                latency_ms=round(latency_ms, 3),
                error=error[:300],
            )
