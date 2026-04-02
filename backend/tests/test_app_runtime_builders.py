from app.core.app_dependency_builders import build_app_runtime_dependencies
from app.core.app_repository_builders import build_app_repositories
from app.core.app_runtime_builders import (
    build_app_repositories as facade_build_app_repositories,
)
from app.core.app_runtime_builders import (
    build_app_runtime as facade_build_app_runtime,
)
from app.core.app_runtime_builders import (
    build_app_runtime_dependencies as facade_build_app_runtime_dependencies,
)
from app.core.app_service_builders import build_app_runtime
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.scoring.rule_based_provider import RuleBasedScoringProvider


class FakeProviderRegistry:
    def __init__(self) -> None:
        self.llm_provider = MockLLMProvider()
        self.stt_provider = None
        self.tts_provider = None
        self.scoring_provider = RuleBasedScoringProvider()

    def get_statuses(self) -> list[object]:
        return []


def test_app_runtime_builder_facade_reexports_split_builders() -> None:
    assert facade_build_app_repositories is build_app_repositories
    assert facade_build_app_runtime_dependencies is build_app_runtime_dependencies
    assert facade_build_app_runtime is build_app_runtime


def test_split_app_runtime_builders_construct_runtime_graph(empty_session_factory) -> None:
    repositories = build_app_repositories(empty_session_factory)
    dependencies = build_app_runtime_dependencies(
        repositories,
        empty_session_factory,
        provider_registry=FakeProviderRegistry(),
    )
    runtime = build_app_runtime(repositories, dependencies)

    assert runtime.profile_service is dependencies.profile_service
    assert runtime.recommendation_service is not None
    assert runtime.adaptive_study_service is not None
    assert runtime.user_service is not None
