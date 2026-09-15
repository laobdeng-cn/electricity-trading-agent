from typing import Any


class DecisionAgent:
    """Deterministic decision layer built on market and risk analyses."""

    def __call__(
        self,
        market_analysis: dict[str, Any],
        risk_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        signal = str(market_analysis.get("signal", "insufficient_data"))
        risk_level = str(risk_analysis.get("risk_level", "high"))
        risk_score = int(risk_analysis.get("risk_score", 100))

        if risk_level == "high":
            action = "avoid"
            reason = "风险等级较高，优先规避交易暴露。"
        elif signal == "bullish":
            action = "cautious_buy"
            reason = "市场信号偏多，但仍需受风险等级约束。"
        elif signal == "bearish":
            action = "cautious_sell"
            reason = "市场信号偏空，但仍需受风险等级约束。"
        else:
            action = "observe"
            reason = "市场方向不充分或接近中性，暂不形成方向性动作。"

        summary = (
            f"决策动作 {action}；市场信号 {signal}；"
            f"风险等级 {risk_level}（{risk_score}/100）。{reason}"
        )

        return {
            "action": action,
            "market_signal": signal,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "reason": reason,
            "summary": summary,
        }
