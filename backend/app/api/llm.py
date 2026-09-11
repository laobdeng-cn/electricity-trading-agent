from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_llm_market_analysis_service
from app.llm.deepseek import LLMClientError, LLMConfigurationError
from app.schemas.llm import LLMMarketAnalysisResponse
from app.services.llm_analysis import LLMMarketAnalysisService


router = APIRouter(
    prefix="/market-data",
    tags=["LLM Analysis"],
)


@router.post(
    "/{market_data_id}/llm-analysis",
    response_model=LLMMarketAnalysisResponse,
)
def analyze_market_data_with_llm(
    market_data_id: int,
    service: Annotated[
        LLMMarketAnalysisService,
        Depends(get_llm_market_analysis_service),
    ],
) -> LLMMarketAnalysisResponse:
    try:
        result = service.analyze_market_data(market_data_id)
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except LLMClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market data not found",
        )

    return result
