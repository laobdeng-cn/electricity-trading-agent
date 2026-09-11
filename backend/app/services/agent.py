from typing import Any, Protocol

from pydantic import ValidationError

from app.llm.deepseek import LLMClientError
from app.schemas.agent import (
    AgentChatResponse,
    AnalyzeMarketToolArgs,
)
from app.services.analysis import MarketAnalysisService


class AgentRunner(Protocol):
    def run(
        self,
        message: str,
        tool_executor,
    ) -> AgentChatResponse:
        ...


class MarketAgentService:
    def __init__(
        self,
        analysis_service: MarketAnalysisService,
        agent_runner: AgentRunner,
    ) -> None:
        self.analysis_service = analysis_service
        self.agent_runner = agent_runner

    def chat(self, message: str) -> AgentChatResponse:
        return self.agent_runner.run(
            message=message,
            tool_executor=self.execute_tool,
        )

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        if tool_name != "analyze_market":
            raise LLMClientError(
                f"Unsupported tool requested: {tool_name}"
            )

        try:
            args = AnalyzeMarketToolArgs.model_validate(arguments)
        except ValidationError as exc:
            raise LLMClientError(
                "Invalid analyze_market tool arguments"
            ) from exc

        analysis = self.analysis_service.analyze_market_data(
            args.market_data_id
        )

        if analysis is None:
            return {
                "error": "market_data_not_found",
                "market_data_id": args.market_data_id,
            }

        return analysis.model_dump(mode="json")
