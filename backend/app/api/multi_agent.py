from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.market_analyst import MarketDataNotFoundError
from app.core.dependencies import get_multi_agent_runner
from app.graph.multi_agent_graph import MultiAgentGraphRunner
from app.schemas.multi_agent import (
    MultiAgentAnalyzeRequest,
    MultiAgentAnalyzeResponse,
)


router = APIRouter(
    prefix="/multi-agent",
    tags=["Multi Agent"],
)


@router.post(
    "/analyze",
    response_model=MultiAgentAnalyzeResponse,
)
def analyze_with_multi_agent(
    payload: MultiAgentAnalyzeRequest,
    runner: Annotated[
        MultiAgentGraphRunner,
        Depends(get_multi_agent_runner),
    ],
) -> MultiAgentAnalyzeResponse:
    try:
        state = runner.run(f"分析市场数据 {payload.market_data_id}")
    except MarketDataNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return MultiAgentAnalyzeResponse(
        market_analysis=state["market_analysis"] or {},
        risk_analysis=state["risk_analysis"] or {},
        decision=state["decision_analysis"] or {},
        explanation=state.get("explanation"),
        explanation_status=state.get("explanation_status"),
        explanation_model=state.get("explanation_model"),
        explanation_latency_ms=state.get("explanation_latency_ms"),
        explanation_error=state.get("explanation_error"),
        visited_agents=state["visited_agents"],
        final_answer=state["final_answer"],
    )
