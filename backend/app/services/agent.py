from typing import Any, Protocol

from pydantic import ValidationError

from app.llm.deepseek import LLMClientError
from app.schemas.agent import (
    AgentChatResponse,
    AnalyzeMarketToolArgs,
    CompareMarketDataToolArgs,
    GetMarketDataToolArgs,
)
from app.schemas.market import MarketDataResponse
from app.services.analysis import MarketAnalysisService
from app.services.comparison import MarketComparisonService
from app.services.market import MarketDataService


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
        market_service: MarketDataService,
        analysis_service: MarketAnalysisService,
        comparison_service: MarketComparisonService,
        agent_runner: AgentRunner,
    ) -> None:
        self.market_service = market_service
        self.analysis_service = analysis_service
        self.comparison_service = comparison_service
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
        if tool_name == "get_market_data":
            return self._execute_get_market_data(arguments)

        if tool_name == "analyze_market":
            return self._execute_analyze_market(arguments)

        if tool_name == "compare_market_data":
            return self._execute_compare_market_data(arguments)

        raise LLMClientError(
            f"Unsupported tool requested: {tool_name}"
        )

    def _execute_get_market_data(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            args = GetMarketDataToolArgs.model_validate(arguments)
        except ValidationError as exc:
            raise LLMClientError(
                "Invalid get_market_data tool arguments"
            ) from exc

        market_data = self.market_service.get_market_data(
            args.market_data_id
        )

        if market_data is None:
            return {
                "error": "market_data_not_found",
                "market_data_id": args.market_data_id,
            }

        return MarketDataResponse.model_validate(
            market_data
        ).model_dump(mode="json")

    def _execute_analyze_market(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
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

    def _execute_compare_market_data(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            args = CompareMarketDataToolArgs.model_validate(arguments)
        except ValidationError as exc:
            raise LLMClientError(
                "Invalid compare_market_data tool arguments"
            ) from exc

        comparison = self.comparison_service.compare_market_data(
            args.first_market_data_id,
            args.second_market_data_id,
        )

        if comparison is None:
            return {
                "error": "market_data_not_found",
                "first_market_data_id": args.first_market_data_id,
                "second_market_data_id": args.second_market_data_id,
            }

        return comparison.model_dump(mode="json")
