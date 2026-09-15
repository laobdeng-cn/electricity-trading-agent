from copy import deepcopy
from typing import Any, Protocol


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
