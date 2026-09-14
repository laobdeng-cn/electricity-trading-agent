import json
from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.state import MarketAgentState
from app.schemas.agent import AgentToolExecution


AgentStep = Callable[[list[dict[str, Any]]], dict[str, Any]]
ToolExecutor = Callable[[str, dict[str, Any]], dict[str, Any]]


class MarketAgentGraphRunner:
    """Standalone LangGraph loop used before wiring the production API."""

    def __init__(
        self,
        agent_step: AgentStep,
        tool_executor: ToolExecutor,
        max_steps: int = 6,
    ) -> None:
        self.agent_step = agent_step
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MarketAgentState)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tool_node)
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {
                "tools": "tools",
                "end": END,
            },
        )
        workflow.add_edge("tools", "agent")
        return workflow.compile()

    def run(
        self,
        messages: list[dict[str, Any]],
    ) -> MarketAgentState:
        initial_state: MarketAgentState = {
            "messages": list(messages),
            "pending_tool_calls": [],
            "tool_executions": [],
            "final_answer": None,
            "steps": 0,
        }
        return self.graph.invoke(initial_state)

    def _agent_node(
        self,
        state: MarketAgentState,
    ) -> dict[str, Any]:
        if state["steps"] >= self.max_steps:
            raise RuntimeError("LangGraph agent exceeded maximum steps")

        assistant_message = self.agent_step(state["messages"])
        tool_calls = assistant_message.get("tool_calls") or []
        content = assistant_message.get("content")

        messages = list(state["messages"])
        messages.append(
            {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            }
        )

        final_answer: str | None = None
        if not tool_calls:
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("Agent returned empty final content")
            final_answer = content.strip()

        return {
            "messages": messages,
            "pending_tool_calls": tool_calls,
            "final_answer": final_answer,
            "steps": state["steps"] + 1,
        }

    @staticmethod
    def _route_after_agent(
        state: MarketAgentState,
    ) -> str:
        if state["pending_tool_calls"]:
            return "tools"
        return "end"

    def _tool_node(
        self,
        state: MarketAgentState,
    ) -> dict[str, Any]:
        messages = list(state["messages"])
        executions = list(state["tool_executions"])

        for tool_call in state["pending_tool_calls"]:
            tool_call_id, tool_name, arguments = self._parse_tool_call(
                tool_call
            )
            result = self.tool_executor(tool_name, arguments)

            executions.append(
                AgentToolExecution(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                )
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        return {
            "messages": messages,
            "pending_tool_calls": [],
            "tool_executions": executions,
        }

    @staticmethod
    def _parse_tool_call(
        tool_call: dict[str, Any],
    ) -> tuple[str, str, dict[str, Any]]:
        tool_call_id = str(tool_call["id"])
        function = tool_call["function"]
        tool_name = str(function["name"])
        arguments = json.loads(function["arguments"])

        if not isinstance(arguments, dict):
            raise RuntimeError("Tool arguments must be a JSON object")

        return tool_call_id, tool_name, arguments
