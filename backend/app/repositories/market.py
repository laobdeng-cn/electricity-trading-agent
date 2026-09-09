from datetime import datetime, timezone

from app.schemas.market import (
    MarketDataCreate,
    MarketDataResponse,
)


class MarketDataRepository:
    def __init__(self) -> None:
        self._items: list[MarketDataResponse] = []
        self._next_id: int = 1

    def create(
        self,
        payload: MarketDataCreate,
    ) -> MarketDataResponse:
        market_data = MarketDataResponse(
            id=self._next_id,
            created_at=datetime.now(timezone.utc),
            **payload.model_dump(),
        )

        self._items.append(market_data)
        self._next_id += 1

        return market_data

    def list_all(self) -> list[MarketDataResponse]:
        return list(self._items)

    def get_by_id(
        self,
        market_data_id: int,
    ) -> MarketDataResponse | None:
        for item in self._items:
            if item.id == market_data_id:
                return item

        return None