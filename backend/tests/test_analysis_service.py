from datetime import datetime, timezone

from app.models.market import MarketData
from app.schemas.analysis import MarketSignal
from app.services.analysis import MarketAnalysisService


class FakeMarketDataRepository:
    def __init__(self, market_data: MarketData | None) -> None:
        self.market_data = market_data

    def get_by_id(self, market_data_id: int) -> MarketData | None:
        if self.market_data is None:
            return None

        if self.market_data.id != market_data_id:
            return None

        return self.market_data


def build_market_data(
    *,
    market_data_id: int = 1,
    price: float = 405.2,
    forecast_price: float | None = 412.8,
    load_mw: float = 1420.0,
    renewable_mw: float = 300.0,
) -> MarketData:
    return MarketData(
        id=market_data_id,
        market="day_ahead",
        node="TEST_NODE",
        timestamp=datetime(2026, 9, 10, 6, 0, tzinfo=timezone.utc),
        price=price,
        forecast_price=forecast_price,
        load_mw=load_mw,
        renewable_mw=renewable_mw,
        created_at=datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc),
    )


def test_analyze_market_data_returns_bullish_metrics() -> None:
    repository = FakeMarketDataRepository(build_market_data())
    service = MarketAnalysisService(repository=repository)

    result = service.analyze_market_data(1)

    assert result is not None
    assert result.price_gap == 7.6
    assert result.price_gap_percent == 1.88
    assert result.net_load_mw == 1120.0
    assert result.renewable_ratio_percent == 21.13
    assert result.signal == MarketSignal.BULLISH


def test_analyze_market_data_returns_insufficient_data_without_forecast() -> None:
    repository = FakeMarketDataRepository(
        build_market_data(forecast_price=None)
    )
    service = MarketAnalysisService(repository=repository)

    result = service.analyze_market_data(1)

    assert result is not None
    assert result.price_gap is None
    assert result.price_gap_percent is None
    assert result.signal == MarketSignal.INSUFFICIENT_DATA


def test_analyze_market_data_returns_bearish_signal() -> None:
    repository = FakeMarketDataRepository(
        build_market_data(price=400.0, forecast_price=390.0)
    )
    service = MarketAnalysisService(repository=repository)

    result = service.analyze_market_data(1)

    assert result is not None
    assert result.price_gap == -10.0
    assert result.price_gap_percent == -2.5
    assert result.signal == MarketSignal.BEARISH


def test_analyze_market_data_returns_none_when_record_does_not_exist() -> None:
    repository = FakeMarketDataRepository(None)
    service = MarketAnalysisService(repository=repository)

    result = service.analyze_market_data(999)

    assert result is None
