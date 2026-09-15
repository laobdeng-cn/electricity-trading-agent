from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.multi_agent_state import MultiAgentState


MarketAnalystStep = Callable[[str], dict[str, Any]]
RiskAgentStep = Callable[[dict[str, Any]], dict[str, Any]]
DecisionAgentStep = Callable[
    [dict[str, Any], dict[str, Any]],
    dict[str, Any],
]


class MultiAgentGraphRunner:
    """Three-agent workflow used before wiring a production endpoint."""

    def __init__(
        self,
        market_analyst: MarketAnalystStep,
        risk_agent: RiskAgentStep,
        decision_agent: DecisionAgentStep,
    ) -> None:
        self.market_analyst = market_analyst
        self.risk_agent = risk_agent
        self.decision_agent = decision_agent
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MultiAgentState)
        workflow.add_node("market_analyst", self._market_analyst_node)
        workflow.add_node("risk", self._risk_node)
        workflow.add_node("decision", self._decision_node)
        workflow.add_edge(START, "market_analyst")
        workflow.add_edge("market_analyst", "risk")
        workflow.add_edge("risk", "decision")
        workflow.add_edge("decision", END)
        return workflow.compile()

    def run(self, request: str) -> MultiAgentState:
        initial_state: MultiAgentState = {
            "request": request,
            "market_analysis": None,
            "risk_analysis": None,
            "decision_analysis": None,
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
        return {
            "risk_analysis": risk_analysis,
            "visited_agents": [
                *state["visited_agents"],
                "risk",
            ],
        }

    def _decision_node(
        self,
        state: MultiAgentState,
    ) -> dict[str, Any]:
        market_analysis = state["market_analysis"]
        risk_analysis = state["risk_analysis"]
        if market_analysis is None or risk_analysis is None:
            raise RuntimeError(
                "Decision agent requires market and risk analyses"
            )

        decision_analysis = self.decision_agent(
            market_analysis,
            risk_analysis,
        )
        summary = decision_analysis.get("summary")
        final_answer = summary if isinstance(summary, str) else None

        return {
            "decision_analysis": decision_analysis,
            "final_answer": final_answer,
            "visited_agents": [
                *state["visited_agents"],
                "decision",
            ],
        }
