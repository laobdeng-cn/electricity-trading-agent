from app.schemas.analysis import MarketAnalysisResponse, MarketSignal
from app.services.comparison import MarketComparisonService


class SequencedAnalysisService:
    def __init__(self, results):
        self.results = list(results)

    def analyze_market_data(self, market_data_id: int):
        if not self.results:
            return None
        return self.results.pop(0)


def build_analysis(
    market_data_id: int,
    node: str,
    price: float,
    forecast_price: float | None,
    net_load_mw: float,
    renewable_ratio_percent: float,
    signal: MarketSignal,
) -> MarketAnalysisResponse:
    price_gap = None
    price_gap_percent = None
    if forecast_price is not None:
        price_gap = round(forecast_price - price, 2)
        price_gap_percent = round(price_gap / price * 100, 2)

    return MarketAnalysisResponse(
        market_data_id=market_data_id,
        node=node,
        price=price,
        forecast_price=forecast_price,
        price_gap=price_gap,
        price_gap_percent=price_gap_percent,
        net_load_mw=net_load_mw,
        renewable_ratio_percent=renewable_ratio_percent,
        signal=signal,
    )


def test_compare_market_data_returns_expected_deltas() -> None:
    first = build_analysis(
        1,
        "MAC_NODE_A",
        388.5,
        None,
        950.0,
        26.92,
        MarketSignal.INSUFFICIENT_DATA,
    )
    second = build_analysis(
        2,
        "MAC_NODE_B",
        405.2,
        412.8,
        1120.0,
        21.13,
        MarketSignal.BULLISH,
    )
    service = MarketComparisonService(
        analysis_service=SequencedAnalysisService([first, second])
    )

    result = service.compare_market_data(1, 2)

    assert result is not None
    assert result.price_delta == 16.7
    assert result.forecast_price_delta is None
    assert result.net_load_delta_mw == 170.0
    assert result.renewable_ratio_delta_percent == -5.79
    assert result.first_signal == MarketSignal.INSUFFICIENT_DATA
    assert result.second_signal == MarketSignal.BULLISH


def test_compare_market_data_returns_none_when_record_missing() -> None:
    first = build_analysis(
        1,
        "MAC_NODE_A",
        388.5,
        None,
        950.0,
        26.92,
        MarketSignal.INSUFFICIENT_DATA,
    )
    service = MarketComparisonService(
        analysis_service=SequencedAnalysisService([first, None])
    )

    assert service.compare_market_data(1, 999) is None
