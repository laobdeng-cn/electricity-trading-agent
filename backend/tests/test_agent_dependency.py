from app.core.dependencies import get_market_agent_service
from app.graph.deepseek_market_agent import DeepSeekMarketAgentGraphRunner


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
