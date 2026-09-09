from app.models.market import MarketData
from app.repositories.market import MarketDataRepository
from app.schemas.market import MarketDataCreate


class MarketDataService:
    def __init__(
        self,
        repository: MarketDataRepository,
    ) -> None:
        self.repository = repository

    def create_market_data(
        self,
        payload: MarketDataCreate,
    ) -> MarketData:
        return self.repository.create(payload)

    def list_market_data(self) -> list[MarketData]:
        return self.repository.list_all()

    def get_market_data(
        self,
        market_data_id: int,
    ) -> MarketData | None:
        return self.repository.get_by_id(market_data_id)
