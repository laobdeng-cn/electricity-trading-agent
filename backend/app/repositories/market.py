from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market import MarketData
from app.schemas.market import MarketDataCreate


class MarketDataRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        payload: MarketDataCreate,
    ) -> MarketData:
        market_data = MarketData(
            market=payload.market.value,
            node=payload.node,
            timestamp=payload.timestamp,
            price=payload.price,
            load_mw=payload.load_mw,
            renewable_mw=payload.renewable_mw,
        )

        self.db.add(market_data)
        self.db.commit()
        self.db.refresh(market_data)

        return market_data

    def list_all(self) -> list[MarketData]:
        statement = select(MarketData).order_by(MarketData.id)
        result = self.db.scalars(statement)
        return list(result.all())

    def get_by_id(
        self,
        market_data_id: int,
    ) -> MarketData | None:
        return self.db.get(MarketData, market_data_id)
