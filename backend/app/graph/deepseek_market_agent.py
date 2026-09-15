from collections.abc import Callable
from typing import Any

from app.graph.market_agent_graph import MarketAgentGraphRunner
from app.llm.deepseek import LLMClientError
from app.llm.deepseek_agent import DeepSeekToolCallingClient
from app.schemas.agent import AgentChatResponse


ToolExecutor = Callable[[str, dict[str, Any]], dict[str, Any]]


class DeepSeekMarketAgentGraphRunner:
    """LangGraph adapter around the existing DeepSeek tool-calling client."""

    def __init__(
        self,
        client: DeepSeekToolCallingClient,
        max_steps: int = 6,
    ) -> None:
        self.client = client
        self.max_steps = max_steps

    def run(
        self,
        message: str,
        tool_executor: ToolExecutor,
    ) -> AgentChatResponse:
        graph_runner = MarketAgentGraphRunner(
            agent_step=self.client.request_once,
            tool_executor=tool_executor,
            max_steps=self.max_steps,
        )

        try:
            state = graph_runner.run(
                [
                    {
                        "role": "system",
                        "content": self.client.SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ]
            )
        except RuntimeError as exc:
            if str(exc) == "LangGraph agent exceeded maximum steps":
                raise LLMClientError(
                    "LangGraph agent exceeded maximum steps"
                ) from exc
            raise

        answer = state["final_answer"]
        if not isinstance(answer, str) or not answer.strip():
            raise LLMClientError(
                "LangGraph agent finished without a final answer"
            )

        visited_nodes = state["visited_nodes"]

        return AgentChatResponse(
            answer=answer.strip(),
            model=self.client.model,
            tool_executions=state["tool_executions"],
            steps=len(visited_nodes),
            visited_nodes=visited_nodes,
        )
