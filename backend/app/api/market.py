from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.core.dependencies import get_market_service
from app.schemas.market import (
    MarketDataCreate,
    MarketDataResponse,
)
from app.services.market import MarketDataService


router = APIRouter(
    prefix="/market-data",
    tags=["Market Data"],
)


@router.post(
    "",
    response_model=MarketDataResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_market_data(
    payload: MarketDataCreate,
    service: Annotated[
        MarketDataService,
        Depends(get_market_service),
    ],
) -> MarketDataResponse:
    return service.create_market_data(payload)


@router.get(
    "",
    response_model=list[MarketDataResponse],
)
def list_market_data(
    service: Annotated[
        MarketDataService,
        Depends(get_market_service),
    ],
) -> list[MarketDataResponse]:
    return service.list_market_data()


@router.get(
    "/{market_data_id}",
    response_model=MarketDataResponse,
)
def get_market_data(
    market_data_id: int,
    service: Annotated[
        MarketDataService,
        Depends(get_market_service),
    ],
) -> MarketDataResponse:
    market_data = service.get_market_data(
        market_data_id
    )

    if market_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market data not found",
        )

    return market_data