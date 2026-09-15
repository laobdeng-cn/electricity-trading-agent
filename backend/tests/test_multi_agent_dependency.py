from app.agents.explanation_agent import ResilientExplanationAgent
from app.core.dependencies import get_multi_agent_runner


class FakeAnalysisService:
    pass


def test_multi_agent_dependency_configures_resilient_explanation() -> None:
    runner = get_multi_agent_runner(FakeAnalysisService())

    assert isinstance(
        runner.explanation_agent,
        ResilientExplanationAgent,
    )
