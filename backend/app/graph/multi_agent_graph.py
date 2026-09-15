from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.multi_agent_state import MultiAgentState


MarketAnalystStep = Callable[[str], dict[str, Any]]
RiskAgentStep = Callable[[dict[str, Any]], dict[str, Any]]


class MultiAgentGraphRunner:
    """Minimal two-agent workflow used before wiring a production endpoint."""

    def __init__(
        self,
        market_analyst: MarketAnalystStep,
        risk_agent: RiskAgentStep,
    ) -> None:
        self.market_analyst = market_analyst
        self.risk_agent = risk_agent
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MultiAgentState)
        workflow.add_node("market_analyst", self._market_analyst_node)
        workflow.add_node("risk", self._risk_node)
        workflow.add_edge(START, "market_analyst")
        workflow.add_edge("market_analyst", "risk")
        workflow.add_edge("risk", END)
        return workflow.compile()

    def run(self, request: str) -> MultiAgentState:
        initial_state: MultiAgentState = {
            "request": request,
            "market_analysis": None,
            "risk_analysis": None,
            "final_answer": None,
            "visited_agents": [],
        }
        return self.graph.invoke(initial_state)

    def _market_analyst_node(
        self,
        state: MultiAgentState,
    ) -> dict[str, Any]:
        analysis = self.market_analyst(state["request"])
        return {
            "market_analysis": analysis,
            "visited_agents": [
                *state["visited_agents"],
                "market_analyst",
            ],
        }

    def _risk_node(
        self,
        state: MultiAgentState,
    ) -> dict[str, Any]:
        market_analysis = state["market_analysis"]
        if market_analysis is None:
            raise RuntimeError(
                "Risk agent requires market analysis before execution"
            )

        risk_analysis = self.risk_agent(market_analysis)
        summary = risk_analysis.get("summary")
        final_answer = summary if isinstance(summary, str) else None

        return {
            "risk_analysis": risk_analysis,
            "final_answer": final_answer,
            "visited_agents": [
                *state["visited_agents"],
                "risk",
            ],
        }
