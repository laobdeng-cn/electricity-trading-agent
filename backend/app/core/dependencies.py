from app.repositories.market import MarketDataRepository
from app.services.market import MarketDataService


market_repository = MarketDataRepository()


def get_market_service() -> MarketDataService:
    return MarketDataService(
        repository=market_repository
    )