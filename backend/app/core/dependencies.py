from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.agents.decision_agent import DecisionAgent
from app.agents.explanation_agent import (
    ExplanationAgent,
    ResilientExplanationAgent,
)
from app.agents.market_analyst import MarketAnalystAgent
from app.agents.risk_agent import RiskAgent
from app.core.config import settings
from app.db.session import SessionLocal
from app.graph.deepseek_market_agent import DeepSeekMarketAgentGraphRunner
from app.graph.multi_agent_graph import MultiAgentGraphRunner
from app.llm.deepseek import DeepSeekClient
from app.llm.deepseek_agent import DeepSeekToolCallingClient
from app.llm.deepseek_explanation import DeepSeekExplanationProvider
from app.repositories.market import MarketDataRepository
from app.services.agent import MarketAgentService
from app.services.analysis import MarketAnalysisService
from app.services.comparison import MarketComparisonService
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


def get_market_comparison_service(
    analysis_service: Annotated[
        MarketAnalysisService,
        Depends(get_market_analysis_service),
    ],
) -> MarketComparisonService:
    return MarketComparisonService(
        analysis_service=analysis_service,
    )


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
    market_service: Annotated[
        MarketDataService,
        Depends(get_market_service),
    ],
    analysis_service: Annotated[
        MarketAnalysisService,
        Depends(get_market_analysis_service),
    ],
    comparison_service: Annotated[
        MarketComparisonService,
        Depends(get_market_comparison_service),
    ],
) -> MarketAgentService:
    deepseek_client = DeepSeekToolCallingClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
    )
    agent_runner = DeepSeekMarketAgentGraphRunner(
        client=deepseek_client,
    )

    return MarketAgentService(
        market_service=market_service,
        analysis_service=analysis_service,
        comparison_service=comparison_service,
        agent_runner=agent_runner,
    )


def get_multi_agent_runner(
    analysis_service: Annotated[
        MarketAnalysisService,
        Depends(get_market_analysis_service),
    ],
) -> MultiAgentGraphRunner:
    explanation_provider = DeepSeekExplanationProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
    )
    explanation_agent = ResilientExplanationAgent(
        ExplanationAgent(explanation_provider)
    )

    return MultiAgentGraphRunner(
        market_analyst=MarketAnalystAgent(analysis_service),
        risk_agent=RiskAgent(),
        decision_agent=DecisionAgent(),
        explanation_agent=explanation_agent,
    )
