from collections.abc import Callable
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.graph.multi_agent_state import (
    AgentExecutionStatus,
    MultiAgentState,
)


MarketAnalystStep = Callable[[str], dict[str, Any]]
RiskAgentStep = Callable[[dict[str, Any]], dict[str, Any]]
DecisionAgentStep = Callable[
    [dict[str, Any], dict[str, Any]],
    dict[str, Any],
]
ExplanationAgentStep = Callable[
    [dict[str, Any], dict[str, Any], dict[str, Any]],
    str,
]


class MultiAgentGraphRunner:
    """Deterministic market/risk/decision workflow with optional explanation."""

    def __init__(
        self,
        market_analyst: MarketAnalystStep,
        risk_agent: RiskAgentStep,
        decision_agent: DecisionAgentStep,
        explanation_agent: ExplanationAgentStep | None = None,
    ) -> None:
        self.market_analyst = market_analyst
        self.risk_agent = risk_agent
        self.decision_agent = decision_agent
        self.explanation_agent = explanation_agent
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MultiAgentState)
        workflow.add_node("market_analyst", self._market_analyst_node)
        workflow.add_node("risk", self._risk_node)
        workflow.add_node("decision", self._decision_node)
        workflow.add_edge(START, "market_analyst")
        workflow.add_edge("market_analyst", "risk")
        workflow.add_edge("risk", "decision")

        if self.explanation_agent is None:
            workflow.add_edge("decision", END)
        else:
            workflow.add_node("explanation", self._explanation_node)
            workflow.add_edge("decision", "explanation")
            workflow.add_edge("explanation", END)

        return workflow.compile()

    def run(self, request: str) -> MultiAgentState:
        initial_state: MultiAgentState = {
            "request": request,
            "workflow_id": str(uuid4()),
            "workflow_started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "market_analysis": None,
            "risk_analysis": None,
            "decision_analysis": None,
            "explanation": None,
            "explanation_status": None,
            "explanation_model": None,
            "explanation_latency_ms": None,
            "explanation_error": None,
            "workflow_latency_ms": None,
            "agent_latency_ms": {},
            "agent_status": {},
            "final_answer": None,
            "visited_agents": [],
        }
        started_at = perf_counter()
        result = self.graph.invoke(initial_state)
        result["workflow_latency_ms"] = round(
            (perf_counter() - started_at) * 1000,
            3,
        )
        return result

    @staticmethod
    def _with_latency(
        state: MultiAgentState,
        agent_name: str,
        started_at: float,
    ) -> dict[str, float]:
        return {
            **state["agent_latency_ms"],
            agent_name: round((perf_counter() - started_at) * 1000, 3),
        }

    @staticmethod
    def _with_status(
        state: MultiAgentState,
        agent_name: str,
        status: AgentExecutionStatus,
    ) -> dict[str, AgentExecutionStatus]:
        return {
            **state["agent_status"],
            agent_name: status,
        }

    def _market_analyst_node(
        self,
        state: MultiAgentState,
    ) -> dict[str, Any]:
        started_at = perf_counter()
        try:
            analysis = self.market_analyst(state["request"])
        except Exception:
            state["agent_status"] = self._with_status(
                state,
                "market_analyst",
                "failed",
            )
            raise

        return {
            "market_analysis": analysis,
            "agent_latency_ms": self._with_latency(
                state,
                "market_analyst",
                started_at,
            ),
            "agent_status": self._with_status(
                state,
                "market_analyst",
                "success",
            ),
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
            state["agent_status"] = self._with_status(
                state,
                "risk",
                "failed",
            )
            raise RuntimeError(
                "Risk agent requires market analysis before execution"
            )

        started_at = perf_counter()
        try:
            risk_analysis = self.risk_agent(market_analysis)
        except Exception:
            state["agent_status"] = self._with_status(
                state,
                "risk",
                "failed",
            )
            raise

        return {
            "risk_analysis": risk_analysis,
            "agent_latency_ms": self._with_latency(
                state,
                "risk",
                started_at,
            ),
            "agent_status": self._with_status(
                state,
                "risk",
                "success",
            ),
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
            state["agent_status"] = self._with_status(
                state,
                "decision",
                "failed",
            )
            raise RuntimeError(
                "Decision agent requires market and risk analyses"
            )

        started_at = perf_counter()
        try:
            decision_analysis = self.decision_agent(
                market_analysis,
                risk_analysis,
            )
        except Exception:
            state["agent_status"] = self._with_status(
                state,
                "decision",
                "failed",
            )
            raise

        summary = decision_analysis.get("summary")
        final_answer = summary if isinstance(summary, str) else None

        return {
            "decision_analysis": decision_analysis,
            "final_answer": final_answer,
            "agent_latency_ms": self._with_latency(
                state,
                "decision",
                started_at,
            ),
            "agent_status": self._with_status(
                state,
                "decision",
                "success",
            ),
            "visited_agents": [
                *state["visited_agents"],
                "decision",
            ],
        }

    def _explanation_node(
        self,
        state: MultiAgentState,
    ) -> dict[str, Any]:
        market_analysis = state["market_analysis"]
        risk_analysis = state["risk_analysis"]
        decision_analysis = state["decision_analysis"]
        if (
            market_analysis is None
            or risk_analysis is None
            or decision_analysis is None
        ):
            state["agent_status"] = self._with_status(
                state,
                "explanation",
                "failed",
            )
            raise RuntimeError(
                "Explanation agent requires market, risk, and decision analyses"
            )
        if self.explanation_agent is None:
            state["agent_status"] = self._with_status(
                state,
                "explanation",
                "failed",
            )
            raise RuntimeError("Explanation agent is not configured")

        started_at = perf_counter()
        try:
            observer = getattr(
                self.explanation_agent,
                "generate_observation",
                None,
            )
            if callable(observer):
                observation = observer(
                    market_analysis,
                    risk_analysis,
                    decision_analysis,
                )
                explanation = observation.explanation
                explanation_status = observation.status
                explanation_model = observation.model
                explanation_latency_ms = observation.latency_ms
                explanation_error = observation.error
            else:
                explanation = self.explanation_agent(
                    market_analysis,
                    risk_analysis,
                    decision_analysis,
                )
                explanation_status = None
                explanation_model = None
                explanation_latency_ms = None
                explanation_error = None
        except Exception:
            state["agent_status"] = self._with_status(
                state,
                "explanation",
                "failed",
            )
            raise

        node_status: AgentExecutionStatus = (
            "fallback"
            if explanation_status == "fallback"
            else "success"
        )

        return {
            "explanation": explanation,
            "explanation_status": explanation_status,
            "explanation_model": explanation_model,
            "explanation_latency_ms": explanation_latency_ms,
            "explanation_error": explanation_error,
            "agent_latency_ms": self._with_latency(
                state,
                "explanation",
                started_at,
            ),
            "agent_status": self._with_status(
                state,
                "explanation",
                node_status,
            ),
            "final_answer": explanation,
            "visited_agents": [
                *state["visited_agents"],
                "explanation",
            ],
        }
