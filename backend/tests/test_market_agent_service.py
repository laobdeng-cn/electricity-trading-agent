from datetime import datetime, timezone

import pytest

from app.llm.deepseek import LLMClientError
from app.schemas.agent import AgentChatResponse, AgentToolExecution
from app.schemas.analysis import MarketAnalysisResponse, MarketSignal
from app.schemas.comparison import MarketComparisonResponse
from app.schemas.market import MarketDataResponse, MarketType
from app.services.agent import MarketAgentService


class FakeMarketService:
    def __init__(self, result: MarketDataResponse | None) -> None:
        self.result = result

    def get_market_data(self, market_data_id: int):
        return self.result


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


class FakeComparisonService:
    def __init__(
        self,
        result: MarketComparisonResponse | None,
    ) -> None:
        self.result = result

    def compare_market_data(self, first_id: int, second_id: int):
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


def build_market_data() -> MarketDataResponse:
    return MarketDataResponse(
        id=2,
        market=MarketType.DAY_AHEAD,
        node="MAC_NODE_B",
        timestamp=datetime(2026, 9, 10, 6, 0, tzinfo=timezone.utc),
        price=405.2,
        forecast_price=412.8,
        load_mw=1420.0,
        renewable_mw=300.0,
        created_at=datetime(2026, 9, 9, 10, 35, tzinfo=timezone.utc),
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


def build_comparison() -> MarketComparisonResponse:
    return MarketComparisonResponse(
        first_market_data_id=1,
        second_market_data_id=2,
        first_node="MAC_NODE_A",
        second_node="MAC_NODE_B",
        price_delta=16.7,
        forecast_price_delta=None,
        net_load_delta_mw=170.0,
        renewable_ratio_delta_percent=-5.79,
        first_signal=MarketSignal.INSUFFICIENT_DATA,
        second_signal=MarketSignal.BULLISH,
    )


def build_service() -> MarketAgentService:
    return MarketAgentService(
        market_service=FakeMarketService(build_market_data()),
        analysis_service=FakeAnalysisService(build_analysis()),
        comparison_service=FakeComparisonService(build_comparison()),
        agent_runner=FakeAgentRunner(),
    )


def test_market_agent_executes_analyze_market_tool() -> None:
    service = build_service()

    response = service.chat("分析市场数据 2")

    assert response.answer == "已分析：分析市场数据 2"
    assert len(response.tool_executions) == 1
    execution = response.tool_executions[0]
    assert execution.tool_name == "analyze_market"
    assert execution.result["market_data_id"] == 2
    assert execution.result["signal"] == "bullish"


def test_get_market_data_tool_returns_raw_record() -> None:
    result = build_service().execute_tool(
        "get_market_data",
        {"market_data_id": 2},
    )

    assert result["id"] == 2
    assert result["node"] == "MAC_NODE_B"
    assert result["price"] == 405.2


def test_compare_market_data_tool_returns_deltas() -> None:
    result = build_service().execute_tool(
        "compare_market_data",
        {
            "first_market_data_id": 1,
            "second_market_data_id": 2,
        },
    )

    assert result["price_delta"] == 16.7
    assert result["net_load_delta_mw"] == 170.0
    assert result["second_signal"] == "bullish"


def test_analyze_market_tool_returns_not_found_result() -> None:
    service = MarketAgentService(
        market_service=FakeMarketService(None),
        analysis_service=FakeAnalysisService(None),
        comparison_service=FakeComparisonService(None),
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
    with pytest.raises(LLMClientError):
        build_service().execute_tool("unknown_tool", {})
