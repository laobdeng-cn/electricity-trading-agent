from app.schemas.comparison import MarketComparisonResponse
from app.services.analysis import MarketAnalysisService


class MarketComparisonService:
    def __init__(
        self,
        analysis_service: MarketAnalysisService,
    ) -> None:
        self.analysis_service = analysis_service

    def compare_market_data(
        self,
        first_market_data_id: int,
        second_market_data_id: int,
    ) -> MarketComparisonResponse | None:
        first = self.analysis_service.analyze_market_data(
            first_market_data_id
        )
        second = self.analysis_service.analyze_market_data(
            second_market_data_id
        )

        if first is None or second is None:
            return None

        forecast_price_delta: float | None = None
        if (
            first.forecast_price is not None
            and second.forecast_price is not None
        ):
            forecast_price_delta = round(
                second.forecast_price - first.forecast_price,
                2,
            )

        renewable_ratio_delta_percent: float | None = None
        if (
            first.renewable_ratio_percent is not None
            and second.renewable_ratio_percent is not None
        ):
            renewable_ratio_delta_percent = round(
                second.renewable_ratio_percent
                - first.renewable_ratio_percent,
                2,
            )

        return MarketComparisonResponse(
            first_market_data_id=first.market_data_id,
            second_market_data_id=second.market_data_id,
            first_node=first.node,
            second_node=second.node,
            price_delta=round(second.price - first.price, 2),
            forecast_price_delta=forecast_price_delta,
            net_load_delta_mw=round(
                second.net_load_mw - first.net_load_mw,
                2,
            ),
            renewable_ratio_delta_percent=(
                renewable_ratio_delta_percent
            ),
            first_signal=first.signal,
            second_signal=second.signal,
        )
