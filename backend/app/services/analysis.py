from app.models.market import MarketData
from app.repositories.market import MarketDataRepository
from app.schemas.analysis import MarketAnalysisResponse, MarketSignal


class MarketAnalysisService:
    SIGNAL_THRESHOLD_PERCENT = 1.0

    def __init__(
        self,
        repository: MarketDataRepository,
    ) -> None:
        self.repository = repository

    def analyze_market_data(
        self,
        market_data_id: int,
    ) -> MarketAnalysisResponse | None:
        market_data = self.repository.get_by_id(market_data_id)

        if market_data is None:
            return None

        return self._build_analysis(market_data)

    def _build_analysis(
        self,
        market_data: MarketData,
    ) -> MarketAnalysisResponse:
        net_load_mw = market_data.load_mw - market_data.renewable_mw

        renewable_ratio_percent = None
        if market_data.load_mw > 0:
            renewable_ratio_percent = round(
                market_data.renewable_mw / market_data.load_mw * 100,
                2,
            )

        price_gap = None
        price_gap_percent = None
        signal = MarketSignal.INSUFFICIENT_DATA

        if market_data.forecast_price is not None:
            price_gap = round(
                market_data.forecast_price - market_data.price,
                2,
            )

            if market_data.price != 0:
                price_gap_percent = round(
                    price_gap / abs(market_data.price) * 100,
                    2,
                )

                if price_gap_percent > self.SIGNAL_THRESHOLD_PERCENT:
                    signal = MarketSignal.BULLISH
                elif price_gap_percent < -self.SIGNAL_THRESHOLD_PERCENT:
                    signal = MarketSignal.BEARISH
                else:
                    signal = MarketSignal.NEUTRAL

        return MarketAnalysisResponse(
            market_data_id=market_data.id,
            node=market_data.node,
            price=market_data.price,
            forecast_price=market_data.forecast_price,
            price_gap=price_gap,
            price_gap_percent=price_gap_percent,
            net_load_mw=round(net_load_mw, 2),
            renewable_ratio_percent=renewable_ratio_percent,
            signal=signal,
        )
