from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.llm.deepseek import DeepSeekClient
from app.llm.deepseek_agent import DeepSeekToolCallingClient
from app.repositories.market import MarketDataRepository
from app.services.agent import MarketAgentService
from app.services.analysis import MarketAnalysisService
from app.services.llm_analysis import LLMMarketAnalysisService
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


def get_market_analysis_service(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> MarketAnalysisService:
    repository = MarketDataRepository(db=db)
    return MarketAnalysisService(repository=repository)


def get_llm_market_analysis_service(
    analysis_service: Annotated[
        MarketAnalysisService,
        Depends(get_market_analysis_service),
    ],
) -> LLMMarketAnalysisService:
    llm_client = DeepSeekClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
    )

    return LLMMarketAnalysisService(
        analysis_service=analysis_service,
        llm_client=llm_client,
    )


def get_market_agent_service(
    analysis_service: Annotated[
        MarketAnalysisService,
        Depends(get_market_analysis_service),
    ],
) -> MarketAgentService:
    agent_runner = DeepSeekToolCallingClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
    )

    return MarketAgentService(
        analysis_service=analysis_service,
        agent_runner=agent_runner,
    )
