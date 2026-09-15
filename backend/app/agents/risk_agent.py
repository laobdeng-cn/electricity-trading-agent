from typing import Any


class RiskAgent:
    """Deterministic risk evaluator for market analysis results."""

    def __call__(self, market_analysis: dict[str, Any]) -> dict[str, Any]:
        score = 0
        factors: list[str] = []

        price_gap_percent = market_analysis.get("price_gap_percent")
        if price_gap_percent is None:
            score += 25
            factors.append("missing_forecast_signal")
        else:
            gap = abs(float(price_gap_percent))
            if gap >= 5:
                score += 30
                factors.append(f"large_price_gap:{gap:.2f}%")
            elif gap >= 2:
                score += 18
                factors.append(f"moderate_price_gap:{gap:.2f}%")
            elif gap >= 1:
                score += 8
                factors.append(f"noticeable_price_gap:{gap:.2f}%")

        net_load_mw = market_analysis.get("net_load_mw")
        if net_load_mw is not None:
            net_load = float(net_load_mw)
            if net_load >= 1500:
                score += 20
                factors.append(f"very_high_net_load:{net_load:.2f}MW")
            elif net_load >= 1000:
                score += 10
                factors.append(f"high_net_load:{net_load:.2f}MW")

        renewable_ratio_percent = market_analysis.get(
            "renewable_ratio_percent"
        )
        if renewable_ratio_percent is not None:
            renewable_ratio = float(renewable_ratio_percent)
            if renewable_ratio >= 50:
                score += 20
                factors.append(
                    f"very_high_renewable_ratio:{renewable_ratio:.2f}%"
                )
            elif renewable_ratio >= 35:
                score += 10
                factors.append(
                    f"high_renewable_ratio:{renewable_ratio:.2f}%"
                )

        if market_analysis.get("signal") == "insufficient_data":
            score += 25
            factors.append("insufficient_market_signal_data")

        score = min(score, 100)
        risk_level = self._risk_level(score)
        summary = self._build_summary(risk_level, score, factors)

        return {
            "risk_level": risk_level,
            "risk_score": score,
            "risk_factors": factors,
            "summary": summary,
        }

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 50:
            return "high"
        if score >= 15:
            return "medium"
        return "low"

    @staticmethod
    def _build_summary(
        risk_level: str,
        score: int,
        factors: list[str],
    ) -> str:
        if not factors:
            return f"风险等级 {risk_level}，评分 {score}/100，未发现显著规则风险。"

        return (
            f"风险等级 {risk_level}，评分 {score}/100；"
            f"主要风险因子：{', '.join(factors)}。"
        )
