from typing import Annotated

from fastapi import APIRouter, Depends

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
    state = runner.run(f"分析市场数据 {payload.market_data_id}")

    return MultiAgentAnalyzeResponse(
        market_analysis=state["market_analysis"] or {},
        risk_analysis=state["risk_analysis"] or {},
        decision=state["decision_analysis"] or {},
        visited_agents=state["visited_agents"],
        final_answer=state["final_answer"],
    )
