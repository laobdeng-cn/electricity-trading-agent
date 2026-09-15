from app.agents.decision_agent import DecisionAgent
from app.agents.market_analyst import MarketAnalystAgent
from app.agents.risk_agent import RiskAgent
from app.core.dependencies import (
    get_market_agent_service,
    get_multi_agent_runner,
)
from app.graph.deepseek_market_agent import DeepSeekMarketAgentGraphRunner
from app.graph.multi_agent_graph import MultiAgentGraphRunner


def test_market_agent_dependency_uses_langgraph_runner() -> None:
    service = get_market_agent_service(
        market_service=object(),
        analysis_service=object(),
        comparison_service=object(),
    )

    assert isinstance(
        service.agent_runner,
        DeepSeekMarketAgentGraphRunner,
    )


def test_multi_agent_dependency_wires_three_agents() -> None:
    runner = get_multi_agent_runner(analysis_service=object())

    assert isinstance(runner, MultiAgentGraphRunner)
    assert isinstance(runner.market_analyst, MarketAnalystAgent)
    assert isinstance(runner.risk_agent, RiskAgent)
    assert isinstance(runner.decision_agent, DecisionAgent)
