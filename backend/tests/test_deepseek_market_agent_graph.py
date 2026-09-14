from typing import Any

from app.graph.deepseek_market_agent import DeepSeekMarketAgentGraphRunner
from app.llm.deepseek_agent import DeepSeekToolCallingClient


class FakeDeepSeekClient(DeepSeekToolCallingClient):
    def __init__(
        self,
        responses: list[dict[str, Any]],
    ) -> None:
        super().__init__(
            api_key="test-key",
            base_url="https://example.invalid",
            model="fake-deepseek",
        )
        self.responses = list(responses)
        self.seen_messages: list[list[dict[str, Any]]] = []

    def _request(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.seen_messages.append(list(messages))
        return self.responses.pop(0)


def test_deepseek_langgraph_runs_tool_cycle() -> None:
    client = FakeDeepSeekClient(
        [
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "analyze_market",
                            "arguments": '{"market_data_id": 2}',
                        },
                    }
                ],
            },
            {
                "content": "市场数据 2 当前为 bullish。",
                "tool_calls": [],
            },
        ]
    )

    def tool_executor(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        assert tool_name == "analyze_market"
        assert arguments == {"market_data_id": 2}
        return {
            "market_data_id": 2,
            "signal": "bullish",
        }

    runner = DeepSeekMarketAgentGraphRunner(client=client)
    response = runner.run(
        "分析市场数据 2",
        tool_executor=tool_executor,
    )

    assert response.answer == "市场数据 2 当前为 bullish。"
    assert response.model == "fake-deepseek"
    assert len(response.tool_executions) == 1
    assert response.tool_executions[0].tool_name == "analyze_market"
    assert response.tool_executions[0].result["signal"] == "bullish"
    assert len(client.seen_messages) == 2
    assert client.seen_messages[0][0]["role"] == "system"
    assert client.seen_messages[0][1]["role"] == "user"
    assert client.seen_messages[1][-1]["role"] == "tool"


def test_deepseek_langgraph_can_answer_without_tool() -> None:
    client = FakeDeepSeekClient(
        [
            {
                "content": "请提供 market_data_id。",
                "tool_calls": [],
            }
        ]
    )

    def unexpected_tool_executor(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        raise AssertionError("tool executor should not be called")

    runner = DeepSeekMarketAgentGraphRunner(client=client)
    response = runner.run(
        "帮我分析市场",
        tool_executor=unexpected_tool_executor,
    )

    assert response.answer == "请提供 market_data_id。"
    assert response.tool_executions == []
    assert len(client.seen_messages) == 1
