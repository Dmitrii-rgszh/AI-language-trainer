from app.repositories.account_mappers import (
    to_provider_preference,
    to_user_account,
    to_user_onboarding,
)
from app.repositories.lesson_mappers import (
    focus_area,
    to_lesson,
    to_lesson_block,
    to_lesson_history_item,
    to_lesson_recommendation,
    to_lesson_run_state,
)
from app.repositories.mappers import (
    SKILL_AREA_TO_PROGRESS_FIELD,
    _focus_area,
    to_lesson as legacy_to_lesson,
    to_lesson_block as legacy_to_lesson_block,
    to_lesson_history_item as legacy_to_lesson_history_item,
    to_lesson_recommendation as legacy_to_lesson_recommendation,
    to_lesson_run_state as legacy_to_lesson_run_state,
    to_mistake as legacy_to_mistake,
    to_progress_snapshot as legacy_to_progress_snapshot,
    to_provider_preference as legacy_to_provider_preference,
    to_user_account as legacy_to_user_account,
    to_user_onboarding as legacy_to_user_onboarding,
    to_user_profile as legacy_to_user_profile,
)
from app.repositories.mistake_mappers import to_mistake
from app.repositories.profile_mappers import to_user_profile
from app.repositories.progress_mappers import (
    SKILL_AREA_TO_PROGRESS_FIELD as DOMAIN_SKILL_AREA_TO_PROGRESS_FIELD,
    to_progress_snapshot,
)


def test_legacy_mappers_module_reexports_domain_specific_functions() -> None:
    assert legacy_to_user_profile is to_user_profile
    assert legacy_to_lesson_block is to_lesson_block
    assert legacy_to_lesson is to_lesson
    assert legacy_to_lesson_recommendation is to_lesson_recommendation
    assert legacy_to_lesson_history_item is to_lesson_history_item
    assert legacy_to_lesson_run_state is to_lesson_run_state
    assert legacy_to_mistake is to_mistake
    assert legacy_to_progress_snapshot is to_progress_snapshot
    assert legacy_to_provider_preference is to_provider_preference
    assert legacy_to_user_account is to_user_account
    assert legacy_to_user_onboarding is to_user_onboarding
    assert _focus_area is focus_area
    assert SKILL_AREA_TO_PROGRESS_FIELD is DOMAIN_SKILL_AREA_TO_PROGRESS_FIELD
