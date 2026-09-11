import pytest

from app.llm.deepseek import LLMClientError
from app.schemas.agent import AgentChatResponse, AgentToolExecution
from app.schemas.analysis import MarketAnalysisResponse, MarketSignal
from app.services.agent import MarketAgentService


class FakeAnalysisService:
    def __init__(
        self,
        result: MarketAnalysisResponse | None,
    ) -> None:
        self.result = result

    def analyze_market_data(
        self,
        market_data_id: int,
    ) -> MarketAnalysisResponse | None:
        return self.result


class FakeAgentRunner:
    def run(self, message, tool_executor) -> AgentChatResponse:
        result = tool_executor(
            "analyze_market",
            {"market_data_id": 2},
        )
        return AgentChatResponse(
            answer=f"已分析：{message}",
            model="fake-model",
            tool_executions=[
                AgentToolExecution(
                    tool_name="analyze_market",
                    arguments={"market_data_id": 2},
                    result=result,
                )
            ],
        )


def build_analysis() -> MarketAnalysisResponse:
    return MarketAnalysisResponse(
        market_data_id=2,
        node="MAC_NODE_B",
        price=405.2,
        forecast_price=412.8,
        price_gap=7.6,
        price_gap_percent=1.88,
        net_load_mw=1120.0,
        renewable_ratio_percent=21.13,
        signal=MarketSignal.BULLISH,
    )


def test_market_agent_executes_analyze_market_tool() -> None:
    service = MarketAgentService(
        analysis_service=FakeAnalysisService(build_analysis()),
        agent_runner=FakeAgentRunner(),
    )

    response = service.chat("分析市场数据 2")

    assert response.answer == "已分析：分析市场数据 2"
    assert len(response.tool_executions) == 1
    execution = response.tool_executions[0]
    assert execution.tool_name == "analyze_market"
    assert execution.result["market_data_id"] == 2
    assert execution.result["signal"] == "bullish"


def test_analyze_market_tool_returns_not_found_result() -> None:
    service = MarketAgentService(
        analysis_service=FakeAnalysisService(None),
        agent_runner=FakeAgentRunner(),
    )

    result = service.execute_tool(
        "analyze_market",
        {"market_data_id": 999},
    )

    assert result == {
        "error": "market_data_not_found",
        "market_data_id": 999,
    }


def test_agent_rejects_unknown_tool() -> None:
    service = MarketAgentService(
        analysis_service=FakeAnalysisService(build_analysis()),
        agent_runner=FakeAgentRunner(),
    )

    with pytest.raises(LLMClientError):
        service.execute_tool("unknown_tool", {})
