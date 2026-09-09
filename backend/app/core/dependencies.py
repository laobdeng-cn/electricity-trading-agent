from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.market import MarketDataRepository
from app.services.market import MarketDataService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_market_service(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> MarketDataService:
    repository = MarketDataRepository(db=db)
    return MarketDataService(repository=repository)
