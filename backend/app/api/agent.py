from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_market_agent_service
from app.llm.deepseek import LLMClientError, LLMConfigurationError
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent import MarketAgentService


router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post(
    "/chat",
    response_model=AgentChatResponse,
)
def chat_with_market_agent(
    payload: AgentChatRequest,
    service: Annotated[
        MarketAgentService,
        Depends(get_market_agent_service),
    ],
) -> AgentChatResponse:
    try:
        return service.chat(payload.message)
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
