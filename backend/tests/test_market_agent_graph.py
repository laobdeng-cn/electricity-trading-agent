from typing import Any

import pytest

from app.graph.market_agent_graph import MarketAgentGraphRunner


class FakeAgentStep:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.calls += 1

        if self.calls == 1:
            return {
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
            }

        return {
            "content": "市场数据 2 分析完成。",
            "tool_calls": [],
        }


def test_langgraph_runs_agent_tool_agent_cycle() -> None:
    agent_step = FakeAgentStep()

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

    runner = MarketAgentGraphRunner(
        agent_step=agent_step,
        tool_executor=tool_executor,
    )

    state = runner.run(
        [{"role": "user", "content": "分析市场数据 2"}]
    )

    assert agent_step.calls == 2
    assert state["final_answer"] == "市场数据 2 分析完成。"
    assert state["steps"] == 2
    assert len(state["tool_executions"]) == 1
    assert state["tool_executions"][0].tool_name == "analyze_market"
    assert state["tool_executions"][0].result["signal"] == "bullish"
    assert state["messages"][-2]["role"] == "tool"
    assert state["messages"][-1]["role"] == "assistant"


def test_langgraph_can_finish_without_tool_call() -> None:
    def direct_agent_step(
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "content": "请提供 market_data_id。",
            "tool_calls": [],
        }

    def unexpected_tool_executor(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        raise AssertionError("tool executor should not be called")

    runner = MarketAgentGraphRunner(
        agent_step=direct_agent_step,
        tool_executor=unexpected_tool_executor,
    )

    state = runner.run(
        [{"role": "user", "content": "帮我分析一下市场"}]
    )

    assert state["final_answer"] == "请提供 market_data_id。"
    assert state["steps"] == 1
    assert state["tool_executions"] == []


def test_langgraph_stops_when_agent_exceeds_max_steps() -> None:
    calls = 0

    def looping_agent_step(
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {
            "content": None,
            "tool_calls": [
                {
                    "id": f"call-{calls}",
                    "type": "function",
                    "function": {
                        "name": "analyze_market",
                        "arguments": '{"market_data_id": 2}',
                    },
                }
            ],
        }

    def tool_executor(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "market_data_id": arguments["market_data_id"],
            "signal": "bullish",
        }

    runner = MarketAgentGraphRunner(
        agent_step=looping_agent_step,
        tool_executor=tool_executor,
        max_steps=2,
    )

    with pytest.raises(
        RuntimeError,
        match="LangGraph agent exceeded maximum steps",
    ):
        runner.run(
            [{"role": "user", "content": "持续分析市场数据 2"}]
        )

    assert calls == 2
