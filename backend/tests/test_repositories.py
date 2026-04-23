from datetime import datetime, timedelta

from app.models.mistake_record import MistakeRecord
from app.repositories.content_repository import ContentRepository
from app.repositories.journey_repository import JourneyRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.listening_repository import ListeningRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.onboarding_repository import OnboardingRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.provider_preference_repository import ProviderPreferenceRepository
from app.repositories.pronunciation_attempt_repository import PronunciationAttemptRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.speaking_attempt_repository import SpeakingAttemptRepository
from app.repositories.user_account_repository import UserAccountRepository, UserIdentityConflictError
from app.repositories.vocabulary_repository import VocabularyRepository
from app.repositories.writing_attempt_repository import WritingAttemptRepository
from app.providers.llm.mock_provider import MockLLMProvider
from app.services.adaptive_study_service.service import AdaptiveStudyService
from app.services.ai_orchestrator import AIOrchestrator
from app.services.diagnostic_service.service import DiagnosticService
from app.services.lesson_runtime_service.service import LessonRuntimeService
from app.services.mistake_extraction_service.service import MistakeExtractionService
from app.services.journey_service.service import JourneyService
from app.services.speaking_service.service import SpeakingService
from app.services.writing_service.service import WritingService
from app.schemas.lesson import BlockResultSubmission
from app.schemas.lesson import CompleteLessonRunRequest, StartLessonRunRequest
from app.schemas.feedback import AITextFeedback
from app.schemas.journey import DailyLoopPlan, SaveOnboardingSessionDraftRequest, StartOnboardingSessionRequest
from app.schemas.onboarding import CompleteOnboardingRequest
from app.schemas.provider import ProviderPreferenceUpdateRequest, ProviderType
from app.schemas.profile import OnboardingAnswers, ProfileUpdateRequest
from app.schemas.mistake import WeakSpot
from app.schemas.adaptive import MistakeResolutionSignal, VocabularyLoopSummary
from app.services.onboarding_service.service import OnboardingService
from app.services.profile_service.service import ProfileService
from app.services.recommendation_service.service import RecommendationService


def test_profile_repository_supports_create_and_update(empty_session_factory) -> None:
    repository = ProfileRepository(empty_session_factory)

    assert repository.get_profile() is None

    created = repository.update_profile(
        ProfileUpdateRequest(
            id="user-test-1",
            name="Nina",
            native_language="ru",
            current_level="A2",
            target_level="B1",
            profession_track="insurance",
            preferred_ui_language="ru",
            preferred_explanation_language="ru",
            lesson_duration=20,
            speaking_priority=7,
            grammar_priority=6,
            profession_priority=8,
            onboarding_answers=OnboardingAnswers(
                learner_persona="parent_or_guardian",
                age_group="child",
                learning_context="school_support",
                primary_goal="school_results",
                secondary_goals=["reading_comprehension", "speaking_confidence"],
                active_skill_focus=["reading", "vocabulary", "speaking"],
                study_preferences=["playful_learning", "short_sessions", "parent_guided"],
                interest_topics=["stories", "games", "school_topics"],
                support_needs=["slower_pace", "more_repetition"],
                notes="Parent-led plan for a younger learner.",
            ),
        )
    )

    assert created.id == "user-test-1"
    assert created.profession_track == "insurance"
    assert created.onboarding_answers.age_group == "child"
    assert "games" in created.onboarding_answers.interest_topics

    updated = repository.update_profile(
        ProfileUpdateRequest(
            id="user-test-1",
            name="Nina K",
            native_language="ru",
            current_level="B1",
            target_level="B2",
            profession_track="banking",
            preferred_ui_language="ru",
            preferred_explanation_language="en",
            lesson_duration=30,
            speaking_priority=8,
            grammar_priority=7,
            profession_priority=9,
            onboarding_answers=OnboardingAnswers(
                learner_persona="self_learner",
                age_group="adult",
                learning_context="career_growth",
                primary_goal="work_communication",
                secondary_goals=["speaking_confidence", "vocabulary_growth"],
                active_skill_focus=["speaking", "writing", "grammar"],
                study_preferences=["deep_sessions", "structured_plan"],
                interest_topics=["work_and_business", "technology"],
                support_needs=["clear_examples", "confidence_support"],
                notes="Reoriented the plan around a career switch.",
            ),
        )
    )

    fetched = repository.get_profile("user-test-1")
    assert fetched is not None
    assert updated.name == "Nina K"
    assert fetched.current_level == "B1"
    assert fetched.profession_track == "banking"
    assert fetched.preferred_explanation_language == "en"
    assert fetched.onboarding_answers.primary_goal == "work_communication"
    assert "writing" in fetched.onboarding_answers.active_skill_focus


def test_onboarding_service_keeps_user_and_answers_in_separate_tables(empty_session_factory) -> None:
    profile_repository = ProfileRepository(empty_session_factory)
    user_repository = UserAccountRepository(empty_session_factory)
    onboarding_repository = OnboardingRepository(empty_session_factory)
    onboarding_service = OnboardingService(
        user_repository,
        onboarding_repository,
        ProfileService(profile_repository),
    )

    completed = onboarding_service.complete_onboarding(
        CompleteOnboardingRequest(
            login="nina",
            email="nina@example.com",
            profile=ProfileUpdateRequest(
                id="temp-profile-id",
                name="Nina",
                native_language="ru",
                current_level="A2",
                target_level="B1",
                profession_track="cross_cultural",
                preferred_ui_language="ru",
                preferred_explanation_language="ru",
                lesson_duration=20,
                speaking_priority=7,
                grammar_priority=6,
                profession_priority=5,
                onboarding_answers=OnboardingAnswers(
                    learner_persona="self_learner",
                    age_group="adult",
                    learning_context="general_english",
                    primary_goal="everyday_communication",
                    secondary_goals=["speaking_confidence"],
                    active_skill_focus=["speaking", "vocabulary"],
                    study_preferences=["short_sessions", "gentle_feedback"],
                    interest_topics=["travel", "culture"],
                    support_needs=["confidence_support"],
                    notes="Personal learner flow.",
                ),
            ),
        )
    )

    saved_user = user_repository.get_user(completed.user.id)
    saved_onboarding = onboarding_repository.get_onboarding(completed.user.id)
    saved_profile = profile_repository.get_profile(completed.user.id)

    assert saved_user is not None
    assert saved_user.login == "nina"
    assert saved_user.email == "nina@example.com"
    assert saved_onboarding is not None
    assert saved_onboarding.answers.primary_goal == "everyday_communication"
    assert saved_profile is not None
    assert saved_profile.id == completed.user.id
    assert saved_profile.profession_track == "cross_cultural"


def test_journey_repository_persists_onboarding_sessions_and_daily_loop_state(empty_session_factory) -> None:
    journey_repository = JourneyRepository(empty_session_factory)
    user = UserAccountRepository(empty_session_factory).resolve_user("journey_user", "journey@example.com")

    session = journey_repository.create_onboarding_session(
        source="proof_lesson",
        proof_lesson_handoff={
            "locale": "ru",
            "scenarioId": "coffee-order",
            "beforePhrase": "I want coffee.",
            "afterPhrase": "I'd like a coffee without sugar.",
            "clarityStatusLabel": "Уже звучит яснее",
            "directions": ["speaking", "vocabulary"],
            "wins": ["Learner completed the first phrase."],
            "createdAt": "2026-04-13T12:00:00",
        },
    )

    saved_session = journey_repository.save_onboarding_draft(
        session.id,
        account_draft={"login": "nina", "email": "nina@example.com"},
        profile_draft={
            "id": "temp-profile",
            "name": "Nina",
            "nativeLanguage": "ru",
            "currentLevel": "A2",
            "targetLevel": "B1",
            "professionTrack": "cross_cultural",
            "preferredUiLanguage": "ru",
            "preferredExplanationLanguage": "ru",
            "lessonDuration": 20,
            "speakingPriority": 8,
            "grammarPriority": 6,
            "professionPriority": 5,
            "onboardingAnswers": {
                "primaryGoal": "everyday_communication",
                "preferredMode": "voice_first",
                "diagnosticReadiness": "soft_start",
                "activeSkillFocus": ["speaking", "vocabulary"],
            },
        },
        current_step=2,
    )

    assert saved_session is not None
    assert saved_session.current_step == 2
    assert saved_session.account_draft.login == "nina"

    state = journey_repository.upsert_journey_state(
        user_id=user.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode="voice_first",
        diagnostic_readiness="soft_start",
        time_budget_minutes=20,
        current_focus_area="speaking",
        current_strategy_summary="Keep the first loop focused on speaking.",
        next_best_action="Open the first guided loop.",
        proof_lesson_handoff={
            "locale": "ru",
            "scenarioId": "coffee-order",
            "beforePhrase": "I want coffee.",
            "afterPhrase": "I'd like a coffee without sugar.",
            "clarityStatusLabel": "Уже звучит яснее",
            "directions": ["speaking", "vocabulary"],
            "wins": ["Learner completed the first phrase."],
            "createdAt": "2026-04-13T12:00:00",
        },
        strategy_snapshot={"focusArea": "speaking"},
        last_daily_plan_id="daily-loop-1",
        onboarding_completed_at=datetime.utcnow(),
    )
    plan = journey_repository.upsert_daily_loop_plan(
        user_id=user.id,
        plan_date_key="2026-04-13",
        stage="first_path",
        session_kind="recommended",
        focus_area="speaking",
        headline="First guided loop",
        summary="Start from one guided speaking loop.",
        why_this_now="The first path is ready to move into daily practice.",
        next_step_hint="Open the loop now.",
        preferred_mode="voice_first",
        time_budget_minutes=20,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Daily speaking loop",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Set the first goal.",
                "durationMinutes": 2,
            }
        ],
    )
    attached_plan = journey_repository.attach_daily_loop_run(plan.id, "run-123")
    completed_plan = journey_repository.complete_daily_loop_plan_by_run(
        user_id=user.id,
        run_id="run-123",
        completion_summary={"score": 82},
    )

    assert state.last_daily_plan_id == "daily-loop-1"
    assert plan.focus_area == "speaking"
    assert attached_plan is not None
    assert attached_plan.lesson_run_id == "run-123"
    assert completed_plan is not None
    assert completed_plan.status == "completed"


def test_onboarding_completion_creates_first_daily_loop_plan(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    user_repository = UserAccountRepository(seeded_session_factory)
    onboarding_repository = OnboardingRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )
    onboarding_service = OnboardingService(
        user_repository,
        onboarding_repository,
        ProfileService(profile_repository),
        journey_service,
    )

    session = journey_service.start_onboarding_session(
        StartOnboardingSessionRequest(
            source="proof_lesson",
            proof_lesson_handoff={
                "locale": "en",
                "scenarioId": "coffee-order",
                "beforePhrase": "I want coffee.",
                "afterPhrase": "I'd like a coffee without sugar.",
                "clarityStatusLabel": "Clearer now",
                "directions": ["speaking", "travel"],
                "wins": ["Completed the proof lesson."],
                "createdAt": "2026-04-13T10:00:00",
            },
        )
    )
    journey_service.save_onboarding_draft(
        session.id,
        SaveOnboardingSessionDraftRequest(
            account_draft={"login": "nina_journey", "email": "nina_journey@example.com"},
            profile_draft=ProfileUpdateRequest(
                id="temp-profile",
                name="Nina",
                native_language="ru",
                current_level="A2",
                target_level="B1",
                profession_track="cross_cultural",
                preferred_ui_language="ru",
                preferred_explanation_language="ru",
                lesson_duration=20,
                speaking_priority=8,
                grammar_priority=6,
                profession_priority=5,
                onboarding_answers=OnboardingAnswers(
                    learner_persona="self_learner",
                    age_group="adult",
                    learning_context="general_english",
                    primary_goal="everyday_communication",
                    preferred_mode="voice_first",
                    diagnostic_readiness="checkpoint_now",
                    active_skill_focus=["speaking", "vocabulary"],
                ),
            ),
            current_step=3,
        ),
    )

    completed = onboarding_service.complete_onboarding(
        CompleteOnboardingRequest(
            login="nina_journey",
            email="nina_journey@example.com",
            session_id=session.id,
            profile=ProfileUpdateRequest(
                id="temp-profile",
                name="Nina",
                native_language="ru",
                current_level="A2",
                target_level="B1",
                profession_track="cross_cultural",
                preferred_ui_language="ru",
                preferred_explanation_language="ru",
                lesson_duration=20,
                speaking_priority=8,
                grammar_priority=6,
                profession_priority=5,
                onboarding_answers=OnboardingAnswers(
                    learner_persona="self_learner",
                    age_group="adult",
                    learning_context="general_english",
                    primary_goal="everyday_communication",
                    preferred_mode="voice_first",
                    diagnostic_readiness="checkpoint_now",
                    active_skill_focus=["speaking", "vocabulary"],
                ),
            ),
        )
    )

    journey_state = journey_repository.get_journey_state(completed.user.id)
    assert journey_state is not None
    assert journey_state.stage == "daily_loop_ready"
    assert journey_state.current_focus_area in {"speaking", "grammar", "travel"}

    daily_plan = journey_repository.get_daily_loop_plan(completed.user.id, datetime.utcnow().date().isoformat())
    assert daily_plan is not None
    assert daily_plan.session_kind == "diagnostic"
    assert daily_plan.steps

    lesson_run = journey_service.start_today_session(completed.profile)
    assert lesson_run.lesson.lesson_type == "diagnostic"

    refreshed_plan = journey_repository.get_daily_loop_plan(completed.user.id, datetime.utcnow().date().isoformat())
    assert refreshed_plan is not None
    assert refreshed_plan.lesson_run_id == lesson_run.run_id

    completed_run = lesson_runtime_repository.complete_lesson_run(
        completed.profile.id,
        lesson_run.run_id,
        84,
        [],
    )
    assert completed_run is not None

    journey_service.register_completed_lesson(completed.profile, completed_run)
    completed_state = journey_repository.get_journey_state(completed.user.id)
    assert completed_state is not None
    assert completed_state.stage == "daily_loop_completed"
    assert completed_state.strategy_snapshot["sessionSummary"]["headline"]
    assert completed_state.strategy_snapshot["sessionSummary"]["strategyShift"]
    assert completed_state.strategy_snapshot["tomorrowPreview"]["focusArea"]
    assert completed_state.strategy_snapshot["tomorrowPreview"]["nextStepHint"]
    assert completed_state.strategy_snapshot["tomorrowPreview"]["continuityMode"]


def test_next_day_plan_follows_persisted_tomorrow_preview(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="speaking",
        current_strategy_summary="Yesterday's route is complete.",
        next_best_action="Review tomorrow's route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "sessionSummary": {
                "outcomeBand": "stable",
                "headline": "This session kept the route stable.",
                "whatWorked": "Speaking response gave the system enough confidence to keep the route connected.",
                "watchSignal": "The system still needs to watch Present Perfect vs Past Simple.",
                "strategyShift": "Tomorrow stays centered on grammar while keeping a light watch on Present Perfect vs Past Simple.",
                "coachNote": "Keep the ritual going.",
                "carryOverSignalLabel": "Speaking response",
                "watchSignalLabel": "Present Perfect vs Past Simple",
                "practiceMixEvaluation": {
                    "leadPracticeKey": "speaking",
                    "leadPracticeTitle": "Speaking practice",
                    "leadOutcome": "held",
                    "leadAverageScore": 83,
                    "strongestPracticeKey": "speaking",
                    "strongestPracticeTitle": "Speaking practice",
                    "strongestPracticeScore": 83,
                    "weakestPracticeKey": "grammar",
                    "weakestPracticeTitle": "Grammar patterning",
                    "weakestPracticeScore": 66,
                    "summaryLine": "Speaking practice carried the route best, while grammar patterning still needs support in the next session.",
                },
            },
            "skillTrajectory": {
                "focusSkill": "pronunciation",
                "direction": "slipping",
                "summary": "Across the last 3 snapshots, pronunciation has been slipping, so the route keeps extra support there.",
                "observedSnapshots": 3,
                "signals": [
                    {
                        "skill": "pronunciation",
                        "direction": "slipping",
                        "deltaScore": -6,
                        "currentScore": 47,
                        "summary": "pronunciation has dropped from 53 to 47 across recent sessions, so the route should give it steadier support.",
                    }
                ],
            },
            "strategyMemory": {
                "focusSkill": "pronunciation",
                "persistenceLevel": "persistent",
                "summary": "Across the last 5 snapshots, pronunciation has stayed persistently weak, so the route should keep it as a durable strategy signal.",
                "observedSnapshots": 5,
                "signals": [
                    {
                        "skill": "pronunciation",
                        "persistenceLevel": "persistent",
                        "averageScore": 49,
                        "latestScore": 47,
                        "lowHits": 4,
                        "summary": "pronunciation stayed under pressure in 4 of the last 5 snapshots, so the route should keep returning there even when one session looks better.",
                    }
                ],
            },
            "tomorrowPreview": {
                "focusArea": "grammar",
                "sessionKind": "recommended",
                "headline": "Tomorrow keeps moving around grammar without dropping speaking response.",
                "reason": "The route stays connected while it protects the weak signal.",
                "nextStepHint": "Return tomorrow and keep the guided route moving while carrying speaking response into the next session.",
                "recommendedLessonTitle": "Tomorrow Guided Loop",
                "continuityMode": "carry_forward",
                "carryOverSignalLabel": "Speaking response",
                "watchSignalLabel": "Present Perfect vs Past Simple",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    next_day_plan = journey_service.get_today_plan(profile)
    refreshed_state = journey_repository.get_journey_state(profile.id)

    assert next_day_plan.focus_area == "grammar"
    assert next_day_plan.recommended_lesson_title == "Tomorrow Guided Loop"
    assert "Speaking response" in next_day_plan.summary
    assert "Present Perfect vs Past Simple" in next_day_plan.why_this_now
    assert "grammar patterning" in next_day_plan.summary.lower()
    assert "pronunciation has been slipping" in next_day_plan.summary.lower()
    assert "persistently weak" in next_day_plan.summary.lower()
    assert next_day_plan.next_step_hint.startswith("Return tomorrow")
    assert "speaking practice carried the route best" in next_day_plan.next_step_hint.lower()
    assert "stay especially deliberate around pronunciation" in next_day_plan.next_step_hint.lower()
    assert "durable strategy focus" in next_day_plan.next_step_hint.lower()
    assert any(step.skill == "grammar" for step in next_day_plan.steps)
    assert any("pronunciation" in step.description.lower() and "slipping" in step.description.lower() for step in next_day_plan.steps)
    assert refreshed_state is not None
    assert refreshed_state.stage == "daily_loop_ready"
    assert refreshed_state.current_focus_area == "grammar"
    assert isinstance(refreshed_state.strategy_snapshot.get("strategyMemory"), dict)
    assert refreshed_state.strategy_snapshot["strategyMemory"]["focusSkill"] == "pronunciation"
    assert refreshed_state.next_best_action == next_day_plan.next_step_hint

    lesson_run = journey_service.start_today_session(profile)
    active_state = journey_repository.get_journey_state(profile.id)
    assert "Speaking response" in lesson_run.lesson.title
    assert "Present Perfect vs Past Simple" in lesson_run.lesson.goal
    assert any(
        "carry forward" in block.instructions.lower() or "keep" in block.instructions.lower()
        for block in lesson_run.lesson.blocks
    )
    assert any("continuity" in (block.payload or {}) for block in lesson_run.lesson.blocks)
    assert any("routeContext" in (block.payload or {}) for block in lesson_run.lesson.blocks)
    assert any(
        isinstance((block.payload or {}).get("continuity"), dict)
        and (block.payload or {})["continuity"].get("weakSpotTitles")
        for block in lesson_run.lesson.blocks
    )
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and (block.payload or {})["routeContext"].get("routeSeedSource") == "tomorrow_preview"
        for block in lesson_run.lesson.blocks
    )
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and "grammar patterning still needs support" in str((block.payload or {})["routeContext"].get("practiceShiftSummary") or "").lower()
        for block in lesson_run.lesson.blocks
    )
    assert active_state is not None
    assert active_state.strategy_snapshot["activePlanSeed"]["source"] == "tomorrow_preview"


def test_route_cadence_memory_softens_reentry_after_missed_days(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        ProgressRepository(seeded_session_factory, lesson_repository),
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    today = datetime.utcnow().date()
    completed_date = (today - timedelta(days=4)).isoformat()
    missed_date_a = (today - timedelta(days=3)).isoformat()
    missed_date_b = (today - timedelta(days=2)).isoformat()

    completed_plan = journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=completed_date,
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="grammar",
        headline="Earlier route",
        summary="Completed route.",
        why_this_now="Earlier route was completed.",
        next_step_hint="Completed route hint.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Earlier route",
        steps=[],
    )
    journey_repository.attach_daily_loop_run(completed_plan.id, "run-cadence-completed")
    journey_repository.complete_daily_loop_plan_by_run(
        user_id=profile.id,
        run_id="run-cadence-completed",
        completion_summary={"score": 81},
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=missed_date_a,
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="speaking",
        headline="Missed route A",
        summary="Missed route A.",
        why_this_now="Missed route A.",
        next_step_hint="Missed route A hint.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Missed route A",
        steps=[],
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=missed_date_b,
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="speaking",
        headline="Missed route B",
        summary="Missed route B.",
        why_this_now="Missed route B.",
        next_step_hint="Missed route B hint.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Missed route B",
        steps=[],
    )

    today_plan = journey_service.get_today_plan(profile)

    assert "restart gently instead of widening immediately" in today_plan.summary.lower()
    assert "short warm re-entry" in today_plan.next_step_hint.lower()
    assert "next 2" in today_plan.summary.lower() or "next 3" in today_plan.summary.lower()
    assert today_plan.estimated_minutes <= 18
    assert len(today_plan.steps) <= 6
    assert today_plan.steps[0].title == "Gentle restart"

    journey_service.start_today_session(profile)
    active_state = journey_repository.get_journey_state(profile.id)

    assert active_state is not None
    cadence_memory = active_state.strategy_snapshot.get("routeCadenceMemory")
    assert isinstance(cadence_memory, dict)
    assert cadence_memory.get("status") == "route_rescue"
    assert "restart gently" in str(cadence_memory.get("summary", "")).lower()
    recovery_memory = active_state.strategy_snapshot.get("routeRecoveryMemory")
    assert isinstance(recovery_memory, dict)
    assert recovery_memory.get("phase") == "route_rebuild"
    assert recovery_memory.get("summary")


def test_recommended_daily_route_builds_strategy_guided_template(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="speaking",
        current_strategy_summary="Today's route is ready.",
        next_best_action="Start today's route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": profile.onboarding_answers.primary_goal,
            "preferredMode": profile.onboarding_answers.preferred_mode,
            "focusArea": "speaking",
            "routeRecoveryMemory": {
                "phase": "skill_repair_cycle",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "focused_support",
                "summary": "Grammar still needs a short repair cycle before the wider path opens again.",
                "actionHint": "Reopen support steps in order.",
                "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    plan = journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="speaking",
        headline="Today's route keeps speaking as the lead signal.",
        summary="Start from a guided speaking route and keep grammar in view.",
        why_this_now="This route should turn recent weak signals into one guided speaking pass instead of random module hopping.",
        next_step_hint="Start today's route and keep the response aligned with the main goal.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Guided speaking route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            },
            {
                "id": "input",
                "skill": "reading",
                "title": "Reading input",
                "description": "Pull one useful text signal before the written response.",
                "durationMinutes": 6,
            },
        ],
    )

    lesson_run = journey_service.start_today_session(profile)
    active_state = journey_repository.get_journey_state(profile.id)
    route_contexts = [
        block.payload.get("routeContext")
        for block in lesson_run.lesson.blocks
        if isinstance(block.payload.get("routeContext"), dict)
    ]
    has_vocabulary_rotation = any("vocabulary" in (context.get("moduleRotationKeys") or []) for context in route_contexts)

    assert lesson_run.lesson.title.endswith("guided route for speaking")
    assert "This route should turn recent weak signals" in lesson_run.lesson.goal
    assert any("routeContext" in (block.payload or {}) for block in lesson_run.lesson.blocks)
    assert route_contexts
    assert any(isinstance(context.get("practiceMix"), list) and context.get("practiceMix") for context in route_contexts)
    if has_vocabulary_rotation:
        assert any(block.block_type == "vocab_block" for block in lesson_run.lesson.blocks)
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and (block.payload or {})["routeContext"].get("whyNow") == plan.why_this_now
        for block in lesson_run.lesson.blocks
    )
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and (block.payload or {})["routeContext"].get("preferredMode") == profile.onboarding_answers.preferred_mode
        for block in lesson_run.lesson.blocks
    )
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and isinstance((block.payload or {})["routeContext"].get("routeRecoveryMemory"), dict)
        for block in lesson_run.lesson.blocks
    )
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and isinstance((block.payload or {})["routeContext"].get("routeReentryProgress"), dict)
        and (block.payload or {})["routeContext"].get("routeReentryNextLabel") == "writing support"
        for block in lesson_run.lesson.blocks
    )
    assert any(
        block.block_type == "writing_block"
        and (block.payload or {}).get("task_id") == "guided-route-writing-support"
        for block in lesson_run.lesson.blocks
    )
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and any(
            isinstance(item, dict)
            and item.get("moduleKey") == "writing"
            and item.get("reason")
            and "active recovery sequence" in str(item.get("reason")).lower()
            for item in ((block.payload or {})["routeContext"].get("practiceMix") or [])
        )
        for block in lesson_run.lesson.blocks
    )
    if any("listening" in (context.get("moduleRotationKeys") or []) for context in route_contexts):
        assert any(block.block_type == "listening_block" for block in lesson_run.lesson.blocks)
    assert any(
        "main goal" in prompt.lower() or profile.onboarding_answers.primary_goal in prompt
        for block in lesson_run.lesson.blocks
        for prompt in ((block.payload or {}).get("prompts") or [])
        if isinstance(prompt, str)
    )
    assert active_state is not None
    assert active_state.strategy_snapshot["activePlanSeed"]["source"] == "daily_loop_plan"
    assert isinstance(active_state.strategy_snapshot.get("learningBlueprint"), dict)
    assert active_state.strategy_snapshot["learningBlueprint"]["currentFocus"] == "speaking"
    assert active_state.strategy_snapshot["learningBlueprint"]["focusPillars"]
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and (block.payload or {})["routeContext"].get("learningBlueprintHeadline")
        for block in lesson_run.lesson.blocks
    )
    assert any(
        isinstance((block.payload or {}).get("routeContext"), dict)
        and (block.payload or {})["routeContext"].get("learningBlueprintNorthStar")
        for block in lesson_run.lesson.blocks
    )


def test_text_first_guided_route_switches_response_block_to_writing(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(update={"preferred_mode": "text_first"})
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Today's route should slow down into a text-first response.",
        next_best_action="Start the text-first guided route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": text_first_profile.onboarding_answers.primary_goal,
            "preferredMode": text_first_profile.onboarding_answers.preferred_mode,
            "focusArea": "grammar",
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=text_first_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="grammar",
        headline="Today's route slows down into a writing-first grammar pass.",
        summary="Use a calmer written response before speaking pressure returns.",
        why_this_now="A text-first pass should stabilize grammar before the route widens again.",
        next_step_hint="Start the text-first route and make the response more structured.",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=text_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Text-first grammar route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            },
            {
                "id": "input",
                "skill": "reading",
                "title": "Reading input",
                "description": "Pull one useful text signal before the written response.",
                "durationMinutes": 6,
            },
        ],
    )

    lesson_run = journey_service.start_today_session(text_first_profile)
    response_block = next(
        (
            block
            for block in lesson_run.lesson.blocks
            if block.block_type == "writing_block"
            and block.payload.get("task_id") == "guided-route-writing-response"
        ),
        None,
    )

    assert response_block is not None
    assert response_block.block_type == "writing_block"
    assert "written response" in response_block.title.lower() or "письмен" in response_block.instructions.lower()
    assert response_block.payload.get("task_id") == "guided-route-writing-response"
    assert isinstance(response_block.payload.get("checklist"), list)
    route_context = response_block.payload.get("routeContext")
    assert isinstance(route_context, dict)
    practice_mix = route_context.get("practiceMix")
    assert isinstance(practice_mix, list) and practice_mix
    writing_item = next((item for item in practice_mix if item.get("moduleKey") == "writing"), None)
    speaking_item = next((item for item in practice_mix if item.get("moduleKey") == "speaking"), None)
    assert writing_item is not None
    if speaking_item is not None:
        assert int(writing_item.get("share") or 0) >= int(speaking_item.get("share") or 0)


def test_text_first_guided_route_can_add_reading_support(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing", "grammar"]}
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="Today's route should reopen through reading input and a calmer written response.",
        next_best_action="Start the text-first route through reading and writing.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": text_first_profile.onboarding_answers.primary_goal,
            "preferredMode": text_first_profile.onboarding_answers.preferred_mode,
            "focusArea": "writing",
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=text_first_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Today's route opens through reading before the written response.",
        summary="Use a calmer text input first, then turn it into a structured written answer.",
        why_this_now="A text-first route should start with reading support before it asks for output.",
        next_step_hint="Read the route note, then build the written response.",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=text_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Text-first reading route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            },
            {
                "id": "input",
                "skill": "reading",
                "title": "Reading input",
                "description": "Pull one useful text signal before the written response.",
                "durationMinutes": 6,
            },
        ],
    )

    today_plan = journey_service.get_today_plan(text_first_profile)
    assert today_plan.task_driven_input is not None
    assert today_plan.task_driven_input.input_route == "/reading"
    assert today_plan.task_driven_input.response_route == "/writing"

    lesson_run = journey_service.start_today_session(text_first_profile)
    reading_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "reading_block"), None)

    assert reading_block is not None
    assert "passage" in {key.lower() for key in reading_block.payload.keys()}
    route_context = reading_block.payload.get("routeContext")
    assert isinstance(route_context, dict)
    assert route_context.get("inputLane") == "reading"
    task_driven_input = route_context.get("taskDrivenInput")
    assert isinstance(task_driven_input, dict)
    assert task_driven_input.get("inputRoute") == "/reading"
    assert task_driven_input.get("responseRoute") == "/writing"
    practice_mix = route_context.get("practiceMix")
    assert isinstance(practice_mix, list) and practice_mix
    reading_item = next((item for item in practice_mix if item.get("moduleKey") == "reading"), None)
    listening_item = next((item for item in practice_mix if item.get("moduleKey") == "listening"), None)
    assert reading_item is not None
    if listening_item is not None:
        assert int(reading_item.get("share") or 0) >= int(listening_item.get("share") or 0)

def test_task_driven_step_completion_updates_follow_up_memory(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="reading",
        current_strategy_summary="Today's route should start from reading and move into a written response.",
        next_best_action="Take the reading input first.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": text_first_profile.onboarding_answers.primary_goal,
            "preferredMode": text_first_profile.onboarding_answers.preferred_mode,
            "focusArea": "reading",
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    updated_state = journey_service.register_task_driven_step(
        profile=text_first_profile,
        input_route="/reading",
        response_route="/writing",
    )

    route_follow_up_memory = updated_state.strategy_snapshot.get("routeFollowUpMemory")
    assert isinstance(route_follow_up_memory, dict)
    assert route_follow_up_memory.get("currentRoute") == "/writing"
    assert route_follow_up_memory.get("currentLabel") == "writing response"
    assert route_follow_up_memory.get("followUpRoute") == "/daily-loop"
    assert route_follow_up_memory.get("followUpLabel") == "daily route"
    assert route_follow_up_memory.get("stageLabel") == "Task-driven handoff"
    assert updated_state.current_focus_area == "writing"
    assert "writing response" in updated_state.next_best_action.lower()


def test_completed_task_driven_route_adds_transfer_evaluation_to_summary_and_tomorrow_preview(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="Today's route should open through reading and then test the written transfer.",
        next_best_action="Open the text-first route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": text_first_profile.onboarding_answers.primary_goal,
            "preferredMode": text_first_profile.onboarding_answers.preferred_mode,
            "focusArea": "writing",
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=text_first_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Today's route opens through reading before the written response.",
        summary="Use a calmer text input first, then turn it into a structured written answer.",
        why_this_now="A text-first route should start with reading support before it asks for output.",
        next_step_hint="Read first, then build the written response.",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=text_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Text-first reading route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            },
            {
                "id": "input",
                "skill": "reading",
                "title": "Reading input",
                "description": "Pull one useful text signal before the written response.",
                "durationMinutes": 6,
            },
        ],
    )

    lesson_run = journey_service.start_today_session(text_first_profile)
    reading_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "reading_block"), None)
    writing_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "writing_block"), None)

    assert reading_block is not None
    assert writing_block is not None

    completed_run = lesson_runtime_repository.complete_lesson_run(
        text_first_profile.id,
        lesson_run.run_id,
        67,
        [
            BlockResultSubmission(
                block_id=reading_block.id,
                user_response_type="text",
                user_response="I caught the main idea and the most useful phrases from the passage.",
                feedback_summary="The reading input was understood well.",
                score=85,
            ),
            BlockResultSubmission(
                block_id=writing_block.id,
                user_response_type="text",
                user_response="Short answer with useful ideas but weak structure.",
                feedback_summary="The written transfer is still unstable.",
                score=61,
            ),
        ],
    )
    assert completed_run is not None

    journey_service.register_completed_lesson(text_first_profile, completed_run)
    completed_state = journey_repository.get_journey_state(text_first_profile.id)

    assert completed_state is not None
    session_summary = completed_state.strategy_snapshot["sessionSummary"]
    task_driven_transfer = session_summary.get("taskDrivenTransferEvaluation")
    assert isinstance(task_driven_transfer, dict)
    assert task_driven_transfer.get("inputRoute") == "/reading"
    assert task_driven_transfer.get("responseRoute") == "/writing"
    assert task_driven_transfer.get("transferOutcome") == "fragile"
    assert "transfer into writing response is still fragile" in str(task_driven_transfer.get("summary", "")).lower()
    assert "reading input" in str(session_summary.get("strategyShift", "")).lower()

    tomorrow_preview = completed_state.strategy_snapshot["tomorrowPreview"]
    assert tomorrow_preview.get("continuityMode") == "task_driven_protect"
    assert "writing response" in str(tomorrow_preview.get("nextStepHint", "")).lower()


def test_task_transfer_window_advances_after_strong_protected_response_pass(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="Protect the writing response lane after the fragile transfer.",
        next_best_action="Return for one protected writing response pass.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "fragile",
                    "summary": "The route captured reading input, but the transfer into writing response is still fragile and needs another controlled pass.",
                }
            },
            "tomorrowPreview": {
                "focusArea": "writing",
                "nextStepHint": "Return tomorrow and keep the route tighter around writing response.",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=text_first_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Today's route protects the written response after reading input.",
        summary="Use reading input first, then keep the written response protected before the route widens.",
        why_this_now="The previous transfer into writing response was still fragile.",
        next_step_hint="Read first, then protect the written response.",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=text_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Protected text-first response route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            },
            {
                "id": "input",
                "skill": "reading",
                "title": "Reading input",
                "description": "Pull one useful text signal before the written response.",
                "durationMinutes": 6,
            },
        ],
    )

    lesson_run = journey_service.start_today_session(text_first_profile)
    reading_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "reading_block"), None)
    writing_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "writing_block"), None)

    assert reading_block is not None
    assert writing_block is not None

    completed_run = lesson_runtime_repository.complete_lesson_run(
        text_first_profile.id,
        lesson_run.run_id,
        86,
        [
            BlockResultSubmission(
                block_id=reading_block.id,
                user_response_type="text",
                user_response="I understood the passage and its tone clearly.",
                feedback_summary="The reading signal stayed stable.",
                score=88,
            ),
            BlockResultSubmission(
                block_id=writing_block.id,
                user_response_type="text",
                user_response="I turned the reading into a clear written response with steady structure.",
                feedback_summary="The written transfer landed cleanly.",
                score=84,
            ),
        ],
    )
    assert completed_run is not None

    journey_service.register_completed_lesson(text_first_profile, completed_run)
    completed_state = journey_repository.get_journey_state(text_first_profile.id)

    assert completed_state is not None
    session_summary = completed_state.strategy_snapshot["sessionSummary"]
    task_driven_transfer = session_summary.get("taskDrivenTransferEvaluation")
    assert isinstance(task_driven_transfer, dict)
    assert task_driven_transfer.get("currentWindowStage") == "protect_response"
    assert task_driven_transfer.get("nextWindowStage") == "ready_to_widen"
    assert task_driven_transfer.get("windowAction") == "advance_to_widen"

    tomorrow_preview = completed_state.strategy_snapshot["tomorrowPreview"]
    assert tomorrow_preview.get("continuityMode") == "task_driven_carry"

    route_recovery_memory = completed_state.strategy_snapshot.get("routeRecoveryMemory")
    assert isinstance(route_recovery_memory, dict)
    assert route_recovery_memory.get("decisionBias") == "task_transfer_window"
    assert route_recovery_memory.get("decisionWindowStage") == "ready_to_widen"


def test_task_transfer_window_can_close_after_strong_widening_pass(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="The route can widen again while keeping the writing response reusable.",
        next_best_action="Return for a broader writing-led route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "held",
                    "summary": "The reading signal carried cleanly into writing response, so the route can trust that transfer.",
                }
            },
            "tomorrowPreview": {
                "focusArea": "writing",
                "nextStepHint": "Return tomorrow and let the broader route lead while writing stays available.",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=text_first_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Today's route widens gently after the earlier protected response work.",
        summary="Use reading input first, then let the written response stay available inside the broader route.",
        why_this_now="The transfer into writing response has already held well enough to try a wider pass.",
        next_step_hint="Read first, then let the broader writing route lead.",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=text_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Widening text-first response route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            },
            {
                "id": "input",
                "skill": "reading",
                "title": "Reading input",
                "description": "Pull one useful text signal before the written response.",
                "durationMinutes": 6,
            },
        ],
    )

    lesson_run = journey_service.start_today_session(text_first_profile)
    reading_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "reading_block"), None)
    writing_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "writing_block"), None)

    assert reading_block is not None
    assert writing_block is not None

    completed_run = lesson_runtime_repository.complete_lesson_run(
        text_first_profile.id,
        lesson_run.run_id,
        89,
        [
            BlockResultSubmission(
                block_id=reading_block.id,
                user_response_type="text",
                user_response="I kept the key ideas from the input in focus.",
                feedback_summary="The reading cue stayed available.",
                score=90,
            ),
            BlockResultSubmission(
                block_id=writing_block.id,
                user_response_type="text",
                user_response="I wrote a full response without losing the input signal.",
                feedback_summary="The broader route still carried the response lane cleanly.",
                score=88,
            ),
        ],
    )
    assert completed_run is not None

    journey_service.register_completed_lesson(text_first_profile, completed_run)
    completed_state = journey_repository.get_journey_state(text_first_profile.id)

    assert completed_state is not None
    session_summary = completed_state.strategy_snapshot["sessionSummary"]
    task_driven_transfer = session_summary.get("taskDrivenTransferEvaluation")
    assert isinstance(task_driven_transfer, dict)
    assert task_driven_transfer.get("currentWindowStage") == "ready_to_widen"
    assert task_driven_transfer.get("nextWindowStage") == "close_window"
    assert task_driven_transfer.get("windowAction") == "close_window"

    tomorrow_preview = completed_state.strategy_snapshot["tomorrowPreview"]
    assert tomorrow_preview.get("continuityMode") == "task_driven_widen"

    route_recovery_memory = completed_state.strategy_snapshot.get("routeRecoveryMemory")
    assert isinstance(route_recovery_memory, dict)
    assert route_recovery_memory.get("phase") == "steady_extension"
    assert not route_recovery_memory.get("decisionBias")

def test_voice_first_guided_route_can_add_pronunciation_support(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(lesson_repository, mistake_repository, vocabulary_repository)
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    voice_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={
                    "preferred_mode": "voice_first",
                    "active_skill_focus": ["pronunciation", "speaking", "profession"],
                }
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=voice_first_profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=voice_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=voice_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=voice_first_profile.lesson_duration,
        current_focus_area="pronunciation",
        current_strategy_summary="Today's route should keep the voice layer active.",
        next_best_action="Start the voice-first route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": voice_first_profile.onboarding_answers.primary_goal,
            "preferredMode": voice_first_profile.onboarding_answers.preferred_mode,
            "focusArea": "pronunciation",
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=voice_first_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="pronunciation",
        headline="Today's route keeps a voice-first pronunciation layer active.",
        summary="Use guided speaking plus a short pronunciation support block.",
        why_this_now="A voice-first route should keep pronunciation close to the main response while the route is still fresh.",
        next_step_hint="Start the route and keep the voice layer active.",
        preferred_mode=voice_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=voice_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Voice-first pronunciation route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            }
        ],
    )

    lesson_run = journey_service.start_today_session(voice_first_profile)
    route_contexts = [
        block.payload.get("routeContext")
        for block in lesson_run.lesson.blocks
        if isinstance(block.payload.get("routeContext"), dict)
    ]

    assert any(block.block_type == "pronunciation_block" for block in lesson_run.lesson.blocks)
    assert route_contexts
    assert any("pronunciation" in (context.get("moduleRotationKeys") or []) for context in route_contexts)
    assert any(
        any(
            isinstance(item, dict) and item.get("moduleKey") == "pronunciation"
            for item in (context.get("practiceMix") or [])
        )
        for context in route_contexts
    )


def test_completed_journey_state_persists_practice_mix_evaluation(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(lesson_repository, mistake_repository, vocabulary_repository)
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    strategy_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={
                    "preferred_mode": "text_first",
                    "active_skill_focus": ["grammar", "writing", "vocabulary"],
                }
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=strategy_profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=strategy_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=strategy_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=strategy_profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Today's route should lean on grammar and writing.",
        next_best_action="Start today's route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": strategy_profile.onboarding_answers.primary_goal,
            "preferredMode": strategy_profile.onboarding_answers.preferred_mode,
            "focusArea": "grammar",
            "strategyMemory": {
                "focusSkill": "grammar",
                "persistenceLevel": "recurring",
                "summary": "Across the last 5 snapshots, grammar keeps resurfacing as a recurring weak area, so the route should revisit it deliberately.",
                "observedSnapshots": 5,
                "signals": [
                    {
                        "skill": "grammar",
                        "persistenceLevel": "recurring",
                        "averageScore": 54,
                        "latestScore": 52,
                        "lowHits": 4,
                        "summary": "grammar stayed under pressure often enough that the route should keep returning there deliberately.",
                    }
                ],
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=strategy_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="grammar",
        headline="Today's route leans on grammar and a calmer writing response.",
        summary="Use grammar plus writing to stabilize the route before widening it.",
        why_this_now="A calmer route should stabilize grammar before speaking pressure widens again.",
        next_step_hint="Start the route and keep the structure clean.",
        preferred_mode=strategy_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=strategy_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Text-first grammar route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            }
        ],
    )

    lesson_run = journey_service.start_today_session(strategy_profile)
    grammar_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "grammar_block"), None)
    writing_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "writing_block"), None)
    vocab_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "vocab_block"), None)

    assert grammar_block is not None
    assert writing_block is not None

    completed_run = lesson_runtime_repository.complete_lesson_run(
        strategy_profile.id,
        lesson_run.run_id,
        78,
        [
            BlockResultSubmission(
                block_id=grammar_block.id,
                user_response_type="text",
                user_response="I have worked with this team since 2022.",
                feedback_summary="Grammar stayed mostly stable.",
                score=84,
            ),
            BlockResultSubmission(
                block_id=writing_block.id,
                user_response_type="text",
                user_response="I have written a short update for the client.",
                feedback_summary="Writing stayed usable but still a little stiff.",
                score=71,
            ),
            *(
                [
                    BlockResultSubmission(
                        block_id=vocab_block.id,
                        user_response_type="text",
                        user_response="I reviewed the active route words.",
                        feedback_summary="Vocabulary recall still needs more repetition.",
                        score=60,
                    )
                ]
                if vocab_block is not None
                else []
            ),
        ],
    )
    assert completed_run is not None
    progress_repository.create_snapshot_for_completed_lesson(strategy_profile, completed_run)

    journey_service.register_completed_lesson(strategy_profile, completed_run)
    completed_state = journey_repository.get_journey_state(strategy_profile.id)

    assert completed_state is not None
    session_summary = completed_state.strategy_snapshot["sessionSummary"]
    practice_evaluation = session_summary.get("practiceMixEvaluation")
    assert isinstance(practice_evaluation, dict)
    assert practice_evaluation.get("leadPracticeKey") in {"grammar", "writing"}
    assert practice_evaluation.get("strongestPracticeKey") == "grammar"
    assert practice_evaluation.get("summaryLine")
    assert practice_evaluation.get("leadOutcome") in {"held", "usable"}
    assert practice_evaluation.get("weakestPracticeKey") in {"writing", "vocabulary"}
    assert practice_evaluation.get("summaryLine") in session_summary.get("strategyShift", "")
    skill_trajectory = completed_state.strategy_snapshot.get("skillTrajectory")
    assert isinstance(skill_trajectory, dict)
    assert skill_trajectory.get("focusSkill")
    assert skill_trajectory.get("summary")
    strategy_memory = completed_state.strategy_snapshot.get("strategyMemory")
    assert isinstance(strategy_memory, dict)
    assert strategy_memory.get("focusSkill")
    assert strategy_memory.get("summary")
    route_cadence_memory = completed_state.strategy_snapshot.get("routeCadenceMemory")
    assert isinstance(route_cadence_memory, dict)
    assert route_cadence_memory.get("status")
    assert route_cadence_memory.get("summary")
    route_recovery_memory = completed_state.strategy_snapshot.get("routeRecoveryMemory")
    assert isinstance(route_recovery_memory, dict)
    assert route_recovery_memory.get("phase")
    assert route_recovery_memory.get("summary")


def test_register_route_reentry_support_step_persists_progression(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(lesson_repository, mistake_repository, vocabulary_repository)
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Use grammar support first, then reopen the rest of the repair route in sequence.",
        next_best_action="Open grammar support first.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "skill_repair_cycle",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "repair_mix",
                "summary": "Grammar still needs a short repair cycle across the next routes before the wider path opens again.",
                "actionHint": "Use grammar support first, then reopen the other support surfaces in order.",
                "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
            }
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-reentry-1",
    )

    updated_state = journey_service.register_route_reentry_support_step(
        profile=profile,
        route="/grammar",
    )

    assert updated_state.stage == "daily_loop_ready"
    progress = updated_state.strategy_snapshot.get("routeReentryProgress")
    assert isinstance(progress, dict)
    assert progress.get("focusSkill") == "grammar"
    assert progress.get("completedRoutes") == ["/grammar"]
    assert progress.get("nextRoute") == "/writing"
    assert progress.get("status") == "active"
    follow_up = updated_state.strategy_snapshot.get("routeFollowUpMemory")
    assert isinstance(follow_up, dict)
    assert follow_up.get("currentRoute") == "/writing"
    assert follow_up.get("followUpRoute") == "/daily-loop"
    assert follow_up.get("followUpLabel") == "daily route"
    assert "writing support" in updated_state.current_strategy_summary.lower()
    assert "writing support" in updated_state.next_best_action.lower()


def test_today_plan_follows_persisted_reentry_next_route(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="The route is still in a grammar repair cycle.",
        next_best_action="Open writing support next.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "skill_repair_cycle",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "focused_support",
                "summary": "Grammar needs a short repair cycle across the next routes before the wider path opens again.",
                "actionHint": "Keep the route narrow and reopen support steps in order.",
                "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-1",
    )

    plan = journey_service.get_today_plan(profile)

    assert plan.focus_area == "writing"
    assert "reopens through writing support" in plan.headline.lower()
    assert "writing support" in plan.summary.lower()
    assert "writing support" in plan.next_step_hint.lower()
    assert any(step.title == "Writing support step" for step in plan.steps)
    assert len(plan.steps) >= 2
    assert plan.steps[1].title == "Writing support step"
    assert plan.ritual is not None
    assert any(stage.emphasis == "closure" for stage in plan.ritual.stages)
    assert "only complete after the final strategic summary" in plan.ritual.completion_rule.lower()


def test_register_route_entry_persists_recent_reentry_history(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Use the next re-entry step without widening too early.",
        next_best_action="Open writing support next.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "skill_repair_cycle",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "focused_support",
                "summary": "Grammar still needs a short repair cycle before the route widens again.",
                "actionHint": "Keep the route narrow and reopen support steps in order.",
                "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-1",
    )

    journey_service.register_route_entry(
        profile=profile,
        route="/writing",
        source="smart_reentry",
    )
    refreshed_state = journey_service.register_route_entry(
        profile=profile,
        route="/writing",
        source="surface_visit",
    )

    route_entry_memory = refreshed_state.strategy_snapshot.get("routeEntryMemory")
    assert isinstance(route_entry_memory, dict)
    assert route_entry_memory.get("lastRoute") == "/writing"
    assert route_entry_memory.get("activeNextRoute") == "/writing"
    assert route_entry_memory.get("activeNextRouteVisits") == 2
    assert route_entry_memory.get("repeatedRouteCount") == 2
    assert route_entry_memory.get("connectedResetVisits") == 0
    assert route_entry_memory.get("readyToReopenActiveNextRoute") is False
    recent_entries = route_entry_memory.get("recentEntries")
    assert isinstance(recent_entries, list)
    assert len(recent_entries) == 2
    assert recent_entries[-1]["source"] == "surface_visit"


def test_register_route_entry_marks_support_ready_after_connected_reset_passes(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Use the calmer main route before reopening writing support again.",
        next_best_action="Use the calmer main route first.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "skill_repair_cycle",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "focused_support",
                "summary": "Grammar still needs a short repair cycle before the route widens again.",
                "actionHint": "Keep the route narrow and reopen support steps in order.",
                "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-1",
    )

    journey_service.register_route_entry(profile=profile, route="/writing", source="smart_reentry")
    journey_service.register_route_entry(profile=profile, route="/writing", source="surface_visit")
    journey_service.register_route_entry(profile=profile, route="/daily-loop", source="surface_visit")
    refreshed_state = journey_service.register_route_entry(
        profile=profile,
        route="/lesson-runner",
        source="surface_visit",
    )

    route_entry_memory = refreshed_state.strategy_snapshot.get("routeEntryMemory")
    assert isinstance(route_entry_memory, dict)
    assert route_entry_memory.get("activeNextRoute") == "/writing"
    assert route_entry_memory.get("activeNextRouteVisits") == 2
    assert route_entry_memory.get("connectedResetVisits") == 2
    assert route_entry_memory.get("readyToReopenActiveNextRoute") is True
    follow_up = refreshed_state.strategy_snapshot.get("routeFollowUpMemory")
    assert isinstance(follow_up, dict)
    assert follow_up.get("currentRoute") == "/writing"
    assert follow_up.get("followUpRoute") == "/daily-loop"
    assert follow_up.get("stageLabel") in {"First reopen", "Settling pass", "Ready to widen", None}
    assert "writing support" in refreshed_state.current_strategy_summary.lower()
    assert "daily route" in refreshed_state.next_best_action.lower()


def test_today_plan_resets_to_main_route_after_repeated_reentry_visits(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Reset through the calmer main route first.",
        next_best_action="Use the calmer main route before reopening writing support again.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "skill_repair_cycle",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "focused_support",
                "summary": "Grammar still needs a short repair cycle before the wider path opens again.",
                "actionHint": "Keep the route narrow and reopen support steps in order.",
                "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeEntryMemory": {
                "recentEntries": [
                    {
                        "route": "/writing",
                        "source": "smart_reentry",
                        "enteredAt": "2026-04-15T10:00:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/writing",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:10:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                ],
                "lastRoute": "/writing",
                "lastSource": "surface_visit",
                "repeatedRouteCount": 2,
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-1",
    )

    plan = journey_service.get_today_plan(profile)

    assert plan.focus_area == "grammar"
    assert "resets through the calmer main path" in plan.headline.lower()
    assert "writing support has already reopened 2 times" in plan.summary.lower()
    assert "calmer main route first" in plan.next_step_hint.lower()
    assert "before trying that support surface again" in plan.summary.lower()


def test_today_plan_reopens_support_after_connected_reset_passes(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="The calmer reset has already landed, so writing support can reopen again.",
        next_best_action="Open writing support next.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "protected_return",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "protected_mix",
                "summary": "The route is reconnecting through the calmer main path before writing support reopens again.",
                "actionHint": "Use connected reset passes before reopening writing support again.",
                "nextPhaseHint": "If the calmer reset holds, writing support can reopen again without trapping the learner.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeEntryMemory": {
                "recentEntries": [
                    {
                        "route": "/writing",
                        "source": "smart_reentry",
                        "enteredAt": "2026-04-15T10:00:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/writing",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:10:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/daily-loop",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:20:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "protected_return",
                        "sessionShape": "protected_mix",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/lesson-runner",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:30:00",
                        "stage": "daily_loop_active",
                        "recoveryPhase": "protected_return",
                        "sessionShape": "protected_mix",
                        "nextRoute": "/writing",
                    },
                ],
                "lastRoute": "/lesson-runner",
                "lastSource": "surface_visit",
                "repeatedRouteCount": 1,
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
                "connectedResetVisits": 2,
                "readyToReopenActiveNextRoute": True,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-1",
    )

    plan = journey_service.get_today_plan(profile)

    assert plan.focus_area == "writing"
    assert "reopens calmly around writing" in plan.headline.lower()
    assert "connected reset has already landed" in plan.summary.lower()
    assert "writing support" in plan.summary.lower()
    assert "writing support" in plan.next_step_hint.lower()
    assert plan.estimated_minutes >= 19
    assert len(plan.steps) >= 6


def test_recommendation_uses_support_reopen_arc_after_connected_reset_passes(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="The calmer reset has already landed, so writing support can reopen again.",
        next_best_action="Open writing support next.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "protected_return",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "protected_mix",
                "summary": "The route is reconnecting through the calmer main path before writing support reopens again.",
                "actionHint": "Use connected reset passes before reopening writing support again.",
                "nextPhaseHint": "If the calmer reset holds, writing support can reopen again without trapping the learner.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeEntryMemory": {
                "recentEntries": [
                    {
                        "route": "/writing",
                        "source": "smart_reentry",
                        "enteredAt": "2026-04-15T10:00:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/writing",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:10:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/daily-loop",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:20:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "protected_return",
                        "sessionShape": "protected_mix",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/lesson-runner",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:30:00",
                        "stage": "daily_loop_active",
                        "recoveryPhase": "protected_return",
                        "sessionShape": "protected_mix",
                        "nextRoute": "/writing",
                    },
                ],
                "lastRoute": "/lesson-runner",
                "lastSource": "surface_visit",
                "repeatedRouteCount": 1,
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
                "connectedResetVisits": 2,
                "readyToReopenActiveNextRoute": True,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    recommendation = recommendation_repository.get_next_step(profile)

    assert recommendation is not None
    assert recommendation.focus_area == "writing"
    assert "support_reopen_arc" in recommendation.goal.lower()
    assert "writing support" in recommendation.goal.lower()
    assert "daily route" in recommendation.goal.lower()


def test_recommendation_widens_when_support_reopen_arc_is_ready_to_expand(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="Writing support has landed and the route can widen again.",
        next_best_action="Return to the broader daily route while keeping writing support available.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "support_reopen_arc",
                "horizonDays": 3,
                "focusSkill": "writing",
                "supportPracticeTitle": "writing support",
                "sessionShape": "guided_balance",
                "summary": "Writing support has already landed across two connected reopen passes, so the next route can widen again without dropping it.",
                "actionHint": "Let the next route widen through the daily route, but keep writing support available inside the broader mix.",
                "nextPhaseHint": "If writing support stays stable in this wider pass, the route can leave the reopen arc and extend forward again.",
                "reopenStage": "ready_to_expand",
                "expansionReady": True,
                "followUpCompletionCount": 2,
                "decisionBias": "widening_window",
                "decisionWindowDays": 2,
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeFollowUpMemory": {
                "currentRoute": "/daily-loop",
                "currentLabel": "daily route",
                "followUpRoute": "/writing",
                "followUpLabel": "writing support",
                "stageLabel": "Ready to widen",
                "status": "active",
                "summary": "The route widens through the daily route first, then keeps writing support available inside the broader flow.",
                "completionCount": 2,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    recommendation = recommendation_repository.get_next_step(profile)

    assert recommendation is not None
    assert "wider" in recommendation.goal.lower() or "widen" in recommendation.goal.lower()
    assert "daily route" in recommendation.goal.lower()
    assert "widens through the daily route first" in recommendation.goal.lower() or "first widening pass" in recommendation.goal.lower()


def test_support_reopen_arc_begins_to_widen_after_recent_reopen_days(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    today = datetime.utcnow().date()
    for offset in (1, 2):
        journey_repository.upsert_daily_loop_plan(
            user_id=profile.id,
            plan_date_key=(today - timedelta(days=offset)).isoformat(),
            stage="daily_loop_completed",
            session_kind="recommended",
            focus_area="writing",
            headline="Writing reopen route",
            summary="A connected writing reopen pass.",
            why_this_now="Keep writing support inside the connected route.",
            next_step_hint="Keep writing support active.",
            preferred_mode=profile.onboarding_answers.preferred_mode,
            time_budget_minutes=profile.lesson_duration,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Writing reopen route",
            steps=[],
            status="completed",
        )

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Writing support has already returned cleanly and the route can start widening again.",
        next_best_action="Keep writing support active, but let the route widen a little.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "protected_return",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "protected_mix",
                "summary": "The route is reconnecting through the calmer main path before writing support reopens again.",
                "actionHint": "Use connected reset passes before reopening writing support again.",
                "nextPhaseHint": "If the calmer reset holds, writing support can reopen again without trapping the learner.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeEntryMemory": {
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
                "connectedResetVisits": 2,
                "readyToReopenActiveNextRoute": True,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-1",
    )

    plan = journey_service.get_today_plan(profile)
    assert plan.focus_area == "writing"
    assert "widen" in plan.summary.lower()
    assert "first widening pass" in plan.summary.lower()
    assert "first widening pass" in plan.next_step_hint.lower()
    assert plan.estimated_minutes >= 18


def test_support_reopen_arc_tracks_stabilizing_widening_after_one_broader_pass(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    today = datetime.utcnow().date()
    for offset in (2, 3):
        journey_repository.upsert_daily_loop_plan(
            user_id=profile.id,
            plan_date_key=(today - timedelta(days=offset)).isoformat(),
            stage="daily_loop_completed",
            session_kind="recommended",
            focus_area="writing",
            headline="Writing reopen route",
            summary="A connected writing reopen pass.",
            why_this_now="Keep writing support inside the connected route.",
            next_step_hint="Keep writing support active.",
            preferred_mode=profile.onboarding_answers.preferred_mode,
            time_budget_minutes=profile.lesson_duration,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Writing reopen route",
            steps=[],
            status="completed",
        )
    journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=(today - timedelta(days=1)).isoformat(),
        stage="daily_loop_completed",
        session_kind="recommended",
        focus_area="grammar",
        headline="Broader daily route",
        summary="A broader widening pass after reopen.",
        why_this_now="Let the daily route lead while writing support stays connected.",
        next_step_hint="Keep the route broad and stable.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Broader daily route",
        steps=[],
        status="completed",
    )

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Writing support has already survived the first wider pass and now needs one more stabilizing wider route.",
        next_best_action="Use one more stabilizing wider route before extending further.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "protected_return",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "protected_mix",
                "summary": "The route is reconnecting through the calmer main path before writing support reopens again.",
                "actionHint": "Use connected reset passes before reopening writing support again.",
                "nextPhaseHint": "If the calmer reset holds, writing support can reopen again without trapping the learner.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeEntryMemory": {
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
                "connectedResetVisits": 2,
                "readyToReopenActiveNextRoute": True,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
        last_daily_plan_id="plan-1",
    )

    plan = journey_service.get_today_plan(profile)
    assert "stabilizing wider pass" in plan.summary.lower() or "stabilize the wider mix" in plan.next_step_hint.lower()
    assert "stabilizing" in plan.why_this_now.lower() or "stabilizing" in plan.next_step_hint.lower()


def test_support_reopen_completion_advances_multi_day_arc(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="The route should reopen through writing support first, then flow back into the connected daily route.",
        next_best_action="Move through writing support now, then continue through daily route so the route stays connected.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "support_reopen_arc",
                "horizonDays": 3,
                "focusSkill": "writing",
                "supportPracticeTitle": "writing support",
                "sessionShape": "protected_mix",
                "summary": "The calmer reset has landed, so the next 3 sessions should reopen through writing support while still protecting writing.",
                "actionHint": "Let writing support come back early inside the next 3 routes, but keep the rest of the route connected.",
                "nextPhaseHint": "If writing support holds cleanly inside the connected route, the recovery arc can widen again without another reset pass.",
                "reopenTargetLabel": "writing support",
                "reopenTargetRoute": "/writing",
                "reopenReady": True,
                "reopenStage": "first_reopen",
            },
            "routeEntryMemory": {
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
                "connectedResetVisits": 2,
                "readyToReopenActiveNextRoute": True,
            },
            "routeFollowUpMemory": {
                "currentRoute": "/writing",
                "currentLabel": "writing support",
                "followUpRoute": "/daily-loop",
                "followUpLabel": "daily route",
                "stageLabel": "First reopen",
                "status": "active",
                "summary": "The route should reopen through writing support first, then flow back into the connected daily route.",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    updated_state = journey_service.register_route_reentry_support_step(
        profile=profile,
        route="/writing",
    )

    follow_up = updated_state.strategy_snapshot.get("routeFollowUpMemory")
    assert isinstance(follow_up, dict)
    assert follow_up.get("completionCount") == 1
    assert follow_up.get("currentRoute") == "/daily-loop"
    assert follow_up.get("stageLabel") == "Settling pass"
    assert "daily route" in updated_state.next_best_action.lower()

    plan = journey_service.get_today_plan(profile)
    refreshed_state = journey_repository.get_journey_state(profile.id)

    assert plan.focus_area == "writing"
    assert "settling pass" in plan.summary.lower()
    assert refreshed_state is not None
    refreshed_recovery = refreshed_state.strategy_snapshot.get("routeRecoveryMemory")
    assert isinstance(refreshed_recovery, dict)
    assert refreshed_recovery.get("reopenStage") == "settling_back_in"
    assert refreshed_recovery.get("followUpCompletionCount") == 1


def test_completed_settling_pass_widens_support_reopen_arc(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
        journey_repository,
    )
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="The route is in a connected settling pass before it widens again.",
        next_best_action="Move through the daily route and let writing support settle inside it.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "support_reopen_arc",
                "horizonDays": 3,
                "focusSkill": "writing",
                "supportPracticeTitle": "writing support",
                "sessionShape": "protected_mix",
                "summary": "Writing support is back, but the route still needs one more connected settling pass before it widens again.",
                "actionHint": "Reconnect through the daily route and keep writing support inside one more controlled pass.",
                "nextPhaseHint": "If this settling pass lands cleanly, the route can widen again while keeping writing support available.",
                "reopenTargetLabel": "writing support",
                "reopenTargetRoute": "/writing",
                "reopenReady": True,
                "reopenStage": "settling_back_in",
                "followUpCompletionCount": 1,
                "decisionBias": "settling_window",
                "decisionWindowDays": 1,
            },
            "routeEntryMemory": {
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
                "connectedResetVisits": 2,
                "readyToReopenActiveNextRoute": True,
            },
            "routeFollowUpMemory": {
                "currentRoute": "/daily-loop",
                "currentLabel": "daily route",
                "followUpRoute": "/writing",
                "followUpLabel": "writing support",
                "stageLabel": "Settling pass",
                "status": "active",
                "summary": "The route should reconnect through the daily route once more, then keep writing support available inside the broader flow.",
                "completionCount": 1,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Today's route keeps one settling pass around writing.",
        summary="Reconnect through the daily route while keeping writing support available inside the flow.",
        why_this_now="This settling pass should tell the system whether writing can widen back into the broader route.",
        next_step_hint="Run the connected settling pass.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Writing settling pass",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Reconnect through the daily route first.",
                "durationMinutes": 2,
            }
        ],
    )

    lesson_run = journey_service.start_today_session(profile)
    writing_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "writing_block"), None)
    grammar_block = next((block for block in lesson_run.lesson.blocks if block.block_type == "grammar_block"), None)

    assert writing_block is not None
    assert grammar_block is not None

    completed_run = lesson_runtime_repository.complete_lesson_run(
        profile.id,
        lesson_run.run_id,
        82,
        [
            BlockResultSubmission(
                block_id=grammar_block.id,
                user_response_type="text",
                user_response="I have updated the client brief and shared the changes clearly.",
                feedback_summary="The daily-route structure stayed stable.",
                score=81,
            ),
            BlockResultSubmission(
                block_id=writing_block.id,
                user_response_type="text",
                user_response="I have written a clearer follow-up for the client and grouped the main points better.",
                feedback_summary="Writing support held cleanly inside the connected route.",
                score=86,
            ),
        ],
    )
    assert completed_run is not None
    progress_repository.create_snapshot_for_completed_lesson(profile, completed_run)

    journey_service.register_completed_lesson(profile, completed_run)
    completed_state = journey_repository.get_journey_state(profile.id)

    assert completed_state is not None
    session_summary = completed_state.strategy_snapshot["sessionSummary"]
    route_recovery_evaluation = session_summary.get("routeRecoveryEvaluation")
    assert isinstance(route_recovery_evaluation, dict)
    assert route_recovery_evaluation.get("currentStage") == "settling_back_in"
    assert route_recovery_evaluation.get("nextStage") == "ready_to_expand"
    assert route_recovery_evaluation.get("completionCount") == 2

    tomorrow_preview = completed_state.strategy_snapshot["tomorrowPreview"]
    assert tomorrow_preview.get("continuityMode") == "reopen_widen"
    assert "broader daily route" in str(tomorrow_preview.get("nextStepHint", "")).lower()


def test_guided_route_softens_repeated_reentry_surface_in_composition(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="Reset through the calmer main route first.",
        next_best_action="Use the calmer main route before reopening writing support again.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": profile.onboarding_answers.primary_goal,
            "preferredMode": profile.onboarding_answers.preferred_mode,
            "focusArea": "grammar",
            "routeRecoveryMemory": {
                "phase": "skill_repair_cycle",
                "horizonDays": 3,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Grammar support",
                "sessionShape": "focused_support",
                "summary": "Grammar still needs a short repair cycle before the wider path opens again.",
                "actionHint": "Keep the route narrow and reopen support steps in order.",
                "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeEntryMemory": {
                "recentEntries": [
                    {
                        "route": "/writing",
                        "source": "smart_reentry",
                        "enteredAt": "2026-04-15T10:00:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                    {
                        "route": "/writing",
                        "source": "surface_visit",
                        "enteredAt": "2026-04-15T10:10:00",
                        "stage": "daily_loop_ready",
                        "recoveryPhase": "skill_repair_cycle",
                        "sessionShape": "focused_support",
                        "nextRoute": "/writing",
                    },
                ],
                "lastRoute": "/writing",
                "lastSource": "surface_visit",
                "repeatedRouteCount": 2,
                "activeNextRoute": "/writing",
                "activeNextRouteVisits": 2,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="grammar",
        headline="Today's route resets through the calmer main path before reopening writing support again.",
        summary="Writing support has already reopened 2 times in recent returns, so today's route resets through the calmer main path first.",
        why_this_now="Use the calmer main route first so the sequence regains momentum before writing support returns.",
        next_step_hint="Use the calmer main route first, then reopen writing support after the route settles again.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Calmer reset route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            }
        ],
    )

    lesson_run = journey_service.start_today_session(profile)
    route_contexts = [
        block.payload.get("routeContext")
        for block in lesson_run.lesson.blocks
        if isinstance(block.payload.get("routeContext"), dict)
    ]

    assert route_contexts
    assert any(context.get("routeEntryResetActive") is True for context in route_contexts)
    assert any(context.get("routeEntryResetLabel") == "writing support" for context in route_contexts)
    assert not any(
        block.block_type == "writing_block"
        and (block.payload or {}).get("task_id") == "guided-route-writing-support"
        for block in lesson_run.lesson.blocks
    )
    assert any(
        any(
            isinstance(item, dict)
            and item.get("moduleKey") == "lesson"
            and "calmer main lesson flow" in str(item.get("reason") or "").lower()
            for item in (context.get("practiceMix") or [])
        )
        for context in route_contexts
    )
    assert any(
        not any(
            isinstance(item, dict) and item.get("moduleKey") == "writing"
            for item in (context.get("practiceMix") or [])
        )
        or any(
            isinstance(item, dict)
            and item.get("moduleKey") == "writing"
            and "reopened repeatedly" in str(item.get("reason") or "").lower()
            for item in (context.get("practiceMix") or [])
        )
        for context in route_contexts
    )


def test_guided_route_uses_widening_window_without_forced_support_block(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="Writing support has landed and the route can widen through the broader daily flow.",
        next_best_action="Use the broader daily route while keeping writing support available inside it.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": profile.onboarding_answers.primary_goal,
            "preferredMode": profile.onboarding_answers.preferred_mode,
            "focusArea": "writing",
            "routeRecoveryMemory": {
                "phase": "support_reopen_arc",
                "horizonDays": 3,
                "focusSkill": "writing",
                "supportPracticeTitle": "writing support",
                "sessionShape": "guided_balance",
                "summary": "Writing support has already landed across two connected reopen passes, so the route can widen again without dropping it.",
                "actionHint": "Let the broader daily route lead again while keeping writing support available inside the mix.",
                "nextPhaseHint": "If writing support stays stable inside the wider route, the reopen arc can phase out into steady extension.",
                "reopenStage": "ready_to_expand",
                "expansionReady": True,
                "followUpCompletionCount": 2,
                "decisionBias": "widening_window",
                "decisionWindowDays": 2,
            },
            "routeReentryProgress": {
                "sequenceKey": "route-reentry:user-local-1:plan-1:skill_repair_cycle:grammar",
                "phase": "skill_repair_cycle",
                "focusSkill": "grammar",
                "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                "completedRoutes": ["/grammar"],
                "nextRoute": "/writing",
                "status": "active",
            },
            "routeFollowUpMemory": {
                "currentRoute": "/daily-loop",
                "currentLabel": "daily route",
                "followUpRoute": "/writing",
                "followUpLabel": "writing support",
                "stageLabel": "Ready to widen",
                "status": "active",
                "summary": "The route widens through the daily route first, then keeps writing support available inside the broader flow.",
                "completionCount": 2,
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Today's route widens through the broader daily flow.",
        summary="Use the daily route as the lead path while keeping writing support available inside a controlled widening window.",
        why_this_now="The reopen arc is ready to widen, so the broader route should lead the next 2 route decisions.",
        next_step_hint="Use the broader daily route first and keep writing support available without letting it dominate.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Widening route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            }
        ],
    )

    lesson_run = journey_service.start_today_session(profile)
    route_contexts = [
        block.payload.get("routeContext")
        for block in lesson_run.lesson.blocks
        if isinstance(block.payload.get("routeContext"), dict)
    ]

    assert route_contexts
    assert any(context.get("routeRecoveryDecisionBias") == "widening_window" for context in route_contexts)
    assert any(context.get("routeRecoveryDecisionWindowDays") == 2 for context in route_contexts)
    assert not any(
        block.block_type == "writing_block"
        and (block.payload or {}).get("task_id") == "guided-route-writing-support"
        for block in lesson_run.lesson.blocks
    )
    assert any(
        any(
            isinstance(item, dict)
            and item.get("moduleKey") == "lesson"
            and item.get("emphasis") == "lead"
            for item in (context.get("practiceMix") or [])
        )
        for context in route_contexts
    )


def test_guided_route_practice_mix_protects_response_lane_after_fragile_task_transfer(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="The route should protect the writing response lane after a fragile reading-to-writing transfer.",
        next_best_action="Return for one more connected writing pass.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "primaryGoal": text_first_profile.onboarding_answers.primary_goal,
            "preferredMode": text_first_profile.onboarding_answers.preferred_mode,
            "focusArea": "writing",
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "fragile",
                    "summary": "The route captured reading input, but the transfer into writing response is still fragile and needs another controlled pass.",
                }
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_repository.upsert_daily_loop_plan(
        user_id=text_first_profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Today's route reuses reading before the written response.",
        summary="Keep the route connected around the written response so the reading signal lands more reliably.",
        why_this_now="The previous input-to-response transfer was still fragile.",
        next_step_hint="Take one more connected writing pass before widening the route.",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=text_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Protected text-first route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            }
        ],
    )

    lesson_run = journey_service.start_today_session(text_first_profile)
    route_contexts = [
        block.payload.get("routeContext")
        for block in lesson_run.lesson.blocks
        if isinstance(block.payload.get("routeContext"), dict)
    ]

    assert route_contexts
    writing_item = next(
        (
            item
            for context in route_contexts
            for item in (context.get("practiceMix") or [])
            if isinstance(item, dict) and item.get("moduleKey") == "writing"
        ),
        None,
    )
    reading_item = next(
        (
            item
            for context in route_contexts
            for item in (context.get("practiceMix") or [])
            if isinstance(item, dict) and item.get("moduleKey") == "reading"
        ),
        None,
    )

    assert writing_item is not None
    assert reading_item is not None
    assert int(writing_item.get("share") or 0) >= int(reading_item.get("share") or 0)
    assert "response lane" in str(writing_item.get("reason", "")).lower()


def test_fragile_task_transfer_creates_protected_response_window_in_next_plan(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="Protect the writing response lane after the fragile transfer.",
        next_best_action="Return for one protected writing response pass.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "fragile",
                    "summary": "The route captured reading input, but the transfer into writing response is still fragile and needs another controlled pass.",
                }
            },
            "tomorrowPreview": {
                "focusArea": "writing",
                "nextStepHint": "Return tomorrow and keep the route tighter around writing response.",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    plan = journey_service.get_today_plan(text_first_profile)
    refreshed_state = journey_repository.get_journey_state(text_first_profile.id)

    assert plan.focus_area == "writing"
    assert "protected" in plan.summary.lower() or "writing response" in plan.summary.lower()
    assert refreshed_state is not None
    route_recovery_memory = refreshed_state.strategy_snapshot.get("routeRecoveryMemory")
    assert isinstance(route_recovery_memory, dict)
    assert route_recovery_memory.get("decisionBias") == "task_transfer_window"
    assert route_recovery_memory.get("decisionWindowStage") == "protect_response"


def test_task_transfer_window_moves_to_stabilizing_after_one_completed_response_day(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None
    text_first_profile = profile.model_copy(
        update={
            "onboarding_answers": profile.onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )

    yesterday = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
    journey_repository.upsert_daily_loop_plan(
        user_id=text_first_profile.id,
        plan_date_key=yesterday,
        stage="daily_loop_completed",
        session_kind="recommended",
        focus_area="writing",
        headline="Protected writing response day",
        summary="One protected response pass around writing.",
        why_this_now="The route was still protecting the transfer into writing response.",
        next_step_hint="Keep the response lane connected.",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        time_budget_minutes=text_first_profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Protected writing response day",
        steps=[],
        status="completed",
    )

    journey_repository.upsert_journey_state(
        user_id=text_first_profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode=text_first_profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=text_first_profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=text_first_profile.lesson_duration,
        current_focus_area="writing",
        current_strategy_summary="Move from protected writing response into one stabilizing pass.",
        next_best_action="Return for one stabilizing writing pass.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "fragile",
                    "summary": "The route captured reading input, but the transfer into writing response is still fragile and needs another controlled pass.",
                }
            },
            "tomorrowPreview": {
                "focusArea": "writing",
                "nextStepHint": "Return for a stabilizing writing response pass.",
            },
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    plan = journey_service.get_today_plan(text_first_profile)
    recommendation = recommendation_repository.get_next_step(text_first_profile)
    refreshed_state = journey_repository.get_journey_state(text_first_profile.id)

    assert refreshed_state is not None
    route_recovery_memory = refreshed_state.strategy_snapshot.get("routeRecoveryMemory")
    assert isinstance(route_recovery_memory, dict)
    assert route_recovery_memory.get("decisionBias") == "task_transfer_window"
    assert route_recovery_memory.get("decisionWindowStage") == "stabilize_transfer"
    assert "stabilizing" in plan.summary.lower() or "stabilizing" in plan.next_step_hint.lower()
    assert recommendation is not None
    assert recommendation.focus_area == "writing"
    assert "stabilizing pass" in recommendation.goal.lower() or "writing response" in recommendation.goal.lower()


def test_user_account_repository_checks_login_availability_and_existing_account(empty_session_factory) -> None:
    repository = UserAccountRepository(empty_session_factory)

    repository.resolve_user("nina", "nina@example.com")

    available = repository.check_login_availability("nina_free")
    taken = repository.check_login_availability("Nina")
    existing_account = repository.check_login_availability("nina", "nina@example.com")

    assert available.available is True
    assert available.status == "available"
    assert taken.available is False
    assert taken.status == "taken"
    assert taken.suggestions
    assert all(suggestion.lower() != "nina" for suggestion in taken.suggestions)
    assert existing_account.available is True
    assert existing_account.status == "existing_account"


def test_user_account_repository_resolve_user_rejects_partial_identity_match(empty_session_factory) -> None:
    repository = UserAccountRepository(empty_session_factory)
    repository.resolve_user("nina", "nina@example.com")

    try:
        repository.resolve_user("nina", "other@example.com")
        raise AssertionError("Expected login conflict when email differs.")
    except UserIdentityConflictError:
        pass

    try:
        repository.resolve_user("nina_new", "nina@example.com")
        raise AssertionError("Expected email conflict when login differs.")
    except UserIdentityConflictError:
        pass


def test_content_repository_reads_bootstrapped_catalogs(seeded_session_factory) -> None:
    repository = ContentRepository(seeded_session_factory)

    grammar_topics = repository.list_grammar_topics()
    profession_tracks = repository.list_profession_tracks()
    speaking_scenarios = repository.list_speaking_scenarios()
    pronunciation_drills = repository.list_pronunciation_drills()
    writing_task = repository.get_primary_writing_task()

    assert len(grammar_topics) >= 3
    assert any(track.domain == "trainer_skills" for track in profession_tracks)
    assert len(speaking_scenarios) >= 2
    assert len(pronunciation_drills) >= 2
    assert writing_task is not None
    assert writing_task.title


def test_provider_preference_repository_persists_preferences(empty_session_factory) -> None:
    profile_repository = ProfileRepository(empty_session_factory)
    preference_repository = ProviderPreferenceRepository(empty_session_factory)

    profile_repository.update_profile(
        ProfileUpdateRequest(
            id="user-test-2",
            name="Nina",
            native_language="ru",
            current_level="A2",
            target_level="B1",
            profession_track="trainer_skills",
            preferred_ui_language="ru",
            preferred_explanation_language="ru",
            lesson_duration=20,
            speaking_priority=7,
            grammar_priority=6,
            profession_priority=8,
        )
    )

    saved = preference_repository.upsert_preference(
        "user-test-2",
        ProviderType.LLM,
        ProviderPreferenceUpdateRequest(
            selected_provider="mock_llm",
            enabled=True,
            settings={"temperature": 0.2},
        ),
    )

    preferences = preference_repository.list_preferences("user-test-2")
    assert saved.selected_provider == "mock_llm"
    assert preferences[0].provider_type == "llm"
    assert preferences[0].settings["temperature"] == 0.2


def test_progress_and_recommendations_use_seeded_runtime_data(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    recommendation_repository = RecommendationRepository(lesson_repository, mistake_repository, vocabulary_repository)

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    lesson = lesson_repository.get_recommended_lesson(profile.profession_track)
    progress = progress_repository.get_latest_snapshot(profile.id)
    weak_spots = mistake_repository.list_weak_spots(profile.id)
    recommendation = recommendation_repository.get_next_step(profile)

    assert lesson is not None
    assert lesson.id == "template-trainer-daily-flow"
    assert progress is not None
    assert progress.grammar_score == 52
    assert len(progress.history) == 1
    assert [spot.title for spot in weak_spots[:2]] == [
        "Present Perfect vs Past Simple",
        "Feedback language for workshops",
    ]
    assert recommendation is not None
    assert recommendation.lesson_type == "recovery"
    assert "Present Perfect vs Past Simple" in recommendation.goal


def test_lesson_runtime_and_progress_snapshot_flow(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    lesson_runtime_service = LessonRuntimeService(
        lesson_runtime_repository,
        progress_repository,
        mistake_repository,
        MistakeExtractionService(),
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    older_draft = lesson_runtime_repository.start_lesson_run(profile.id, profession_track=profile.profession_track)
    assert older_draft is not None

    started = lesson_runtime_service.start_run(profile, StartLessonRunRequest())
    assert started.status == "in_progress"

    before_count = len(mistake_repository.list_mistakes(profile.id))
    completed = lesson_runtime_service.complete_run(
        profile,
        started.run_id,
        CompleteLessonRunRequest(
            score=82,
            block_results=[
                BlockResultSubmission(
                    block_id=started.lesson.blocks[1].id,
                    user_response_type="text",
                    user_response="I work with this team since 2022.",
                    feedback_summary="Grammar answer submitted.",
                    score=82,
                ),
                BlockResultSubmission(
                    block_id=started.lesson.blocks[3].id,
                    user_response_type="text",
                    user_response="This part is wrong.",
                    feedback_summary="Profession answer submitted.",
                    score=82,
                ),
            ],
        ),
    )
    assert completed.lesson_run.status == "completed"
    assert completed.lesson_run.score == 82

    after_count = len(mistake_repository.list_mistakes(profile.id))
    assert completed.progress.minutes_completed_today >= 25
    assert len(completed.progress.history) >= 2
    assert after_count >= before_count
    assert any(mistake.subtype == "tense-choice" for mistake in completed.mistakes)
    active_after_completion = lesson_runtime_repository.get_active_lesson_run(profile.id)
    assert active_after_completion is None


def test_block_submit_persists_partial_block_progress(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    started = lesson_runtime_repository.start_lesson_run(profile.id, profession_track=profile.profession_track)
    assert started is not None

    updated = lesson_runtime_repository.submit_block_result(
        profile.id,
        started.run_id,
        BlockResultSubmission(
            block_id=started.lesson.blocks[0].id,
            user_response_type="text",
            user_response="I reviewed the weak spots and repeated the correct forms.",
            feedback_summary="Partial save from block runner.",
            score=75,
        ),
    )

    assert updated is not None
    saved_block = next(block for block in updated.block_runs if block.block_id == started.lesson.blocks[0].id)
    assert saved_block.user_response == "I reviewed the weak spots and repeated the correct forms."
    assert saved_block.feedback_summary == "Partial save from block runner."
    assert saved_block.score == 75

    active = lesson_runtime_repository.get_active_lesson_run(profile.id)
    assert active is not None
    active_block = next(block for block in active.block_runs if block.block_id == started.lesson.blocks[0].id)
    assert active_block.user_response == "I reviewed the weak spots and repeated the correct forms."


def test_discard_and_restart_draft_flow(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    lesson_runtime_service = LessonRuntimeService(
        lesson_runtime_repository,
        progress_repository,
        mistake_repository,
        MistakeExtractionService(),
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    started = lesson_runtime_service.start_run(profile, StartLessonRunRequest())
    assert lesson_runtime_repository.get_active_lesson_run(profile.id) is not None

    lesson_runtime_service.discard_run(profile, started.run_id)
    assert lesson_runtime_repository.get_active_lesson_run(profile.id) is None

    restarted = lesson_runtime_service.start_run(profile, StartLessonRunRequest())
    restarted_again = lesson_runtime_service.restart_run(profile, restarted.run_id)
    assert restarted_again.run_id != restarted.run_id
    assert lesson_runtime_repository.get_active_lesson_run(profile.id) is not None


def test_speaking_attempt_repository_persists_history(seeded_session_factory) -> None:
    repository = SpeakingAttemptRepository(seeded_session_factory)

    saved = repository.create_attempt(
        user_id="user-local-1",
        scenario_id="speaking-training-debrief",
        input_mode="voice",
        transcript="The workshop was useful, but I need clearer goals.",
        feedback=AITextFeedback(
            source="ai",
            summary="Уточни goals before the next session.",
            voice_text="Уточни goals before the next session.",
            voice_language="ru",
        ),
    )

    attempts = repository.list_attempts("user-local-1")
    assert saved.input_mode == "voice"
    assert attempts[0].scenario_title == "Training Debrief"
    assert attempts[0].transcript == "The workshop was useful, but I need clearer goals."


def test_pronunciation_attempt_repository_builds_history_and_trends(seeded_session_factory) -> None:
    repository = PronunciationAttemptRepository(seeded_session_factory)

    first = repository.create_attempt(
        user_id="user-local-1",
        drill_id="pron-th-sounds",
        target_text="thank the team for the thoughtful feedback",
        sound_focus="th",
        transcript="tank the team for the thoughtful feedback",
        score=68,
        feedback="Focus on the th sound.",
        weakest_words=["thank"],
        focus_issues=["th"],
    )
    repository.create_attempt(
        user_id="user-local-1",
        drill_id="pron-th-sounds",
        target_text="three trainers shared their progress",
        sound_focus="th",
        transcript="free trainers shared their progress",
        score=64,
        feedback="The opening th sound was weak.",
        weakest_words=["three"],
        focus_issues=["th", "word rhythm"],
    )

    attempts = repository.list_attempts("user-local-1")
    trends = repository.get_trends("user-local-1")

    assert first.sound_focus == "th"
    assert attempts[0].target_text
    assert trends.recent_attempts >= 2
    assert trends.average_score >= 60
    assert trends.weakest_words[0].label in {"thank", "three"}
    assert trends.weakest_sounds[0].label == "th"


def test_writing_attempt_repository_persists_history(seeded_session_factory) -> None:
    repository = WritingAttemptRepository(seeded_session_factory)

    saved = repository.create_attempt(
        user_id="user-local-1",
        task_id="writing-reply-hiring-manager",
        draft="Hello team, the workshop was useful and participants feels more confident now.",
        feedback=AITextFeedback(
            source="ai",
            summary="Исправь agreement в participants feel и сделай ending более конкретным.",
            voice_text="Исправь agreement в participants feel и сделай ending более конкретным.",
            voice_language="ru",
        ),
    )

    attempts = repository.list_attempts("user-local-1")
    assert saved.task_id == "writing-reply-hiring-manager"
    assert attempts
    assert attempts[0].task_title
    assert "participants feels" in attempts[0].draft


def test_speaking_catalog_includes_highlight_lowlight_reflection(seeded_session_factory) -> None:
    repository = ContentRepository(seeded_session_factory)

    scenarios = repository.list_speaking_scenarios()

    ritual = next((scenario for scenario in scenarios if scenario.id == "speaking-highlight-lowlight-reflection"), None)
    assert ritual is not None
    assert ritual.mode == "free"
    assert "highlight" in ritual.title.lower()


def test_ritual_signal_memory_changes_journey_state_and_recommendation(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
        journey_repository,
    )
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="The route is ready for the next connected daily step.",
        next_best_action="Open the next route.",
        proof_lesson_handoff={},
        strategy_snapshot={},
        onboarding_completed_at=datetime.utcnow(),
    )

    updated_state = journey_service.register_ritual_signal(
        profile=profile,
        signal_type="word_journal",
        route="/vocabulary",
        label="keep it light",
        summary="A fresh word journal phrase should come back into the next route before it goes cold.",
    )

    ritual_signal_memory = updated_state.strategy_snapshot.get("ritualSignalMemory")
    assert isinstance(ritual_signal_memory, dict)
    assert ritual_signal_memory["activeSignalType"] == "word_journal"
    assert ritual_signal_memory["recommendedFocus"] == "vocabulary"
    assert updated_state.current_focus_area == "vocabulary"
    assert "word journal" in updated_state.current_strategy_summary.lower()

    recommendation = recommendation_repository.get_next_step(profile)
    assert recommendation is not None
    assert recommendation.focus_area == "vocabulary"
    assert "word journal" in recommendation.goal.lower()

    plan = journey_service.get_today_plan(profile)
    assert "word journal" in plan.summary.lower()
    assert "keep it light" in plan.summary.lower()
    assert "keep it light" in plan.next_step_hint.lower()

    route_context = journey_service._build_guided_route_context(  # noqa: SLF001
        profile=profile,
        plan=plan,
        current_state=updated_state,
        recommendation=recommendation,
        weak_spots=mistake_repository.list_weak_spots(profile.id, limit=3),
        due_vocabulary=vocabulary_repository.list_due_items(profile.id, limit=4),
        continuity_seed=None,
    )
    assert route_context["ritualSignalType"] == "word_journal"
    assert route_context["ritualSignalLabel"] == "keep it light"
    assert any(
        isinstance(item, dict)
        and item.get("moduleKey") == "vocabulary"
        and int(item.get("share") or 0) >= 10
        for item in (route_context.get("practiceMix") or [])
    )


def test_ritual_signal_memory_moves_from_capture_to_reuse_window(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    yesterday = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
    previous_plan = journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=yesterday,
        stage="daily_loop_completed",
        session_kind="recommended",
        focus_area="vocabulary",
        headline="Word journal reuse day",
        summary="Reuse the captured phrase in one connected route.",
        why_this_now="The word journal signal should land once in real output.",
        next_step_hint="Reuse the captured phrase once.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Word journal reuse day",
        steps=[],
    )
    journey_repository.attach_daily_loop_run(previous_plan.id, "run-word-journal-1")
    journey_repository.complete_daily_loop_plan_by_run(
        user_id=profile.id,
        run_id="run-word-journal-1",
        completion_summary={"score": 81},
    )

    recorded_at = (datetime.utcnow() - timedelta(days=2)).isoformat()
    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="vocabulary",
        current_strategy_summary="Keep the fresh phrase moving.",
        next_best_action="Reuse the captured phrase once.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "ritualSignalMemory": {
                "activeSignalType": "word_journal",
                "activeRoute": "/vocabulary",
                "activeLabel": "keep it light",
                "recommendedFocus": "vocabulary",
                "signalCount": 1,
                "windowDays": 2,
                "windowStage": "fresh_capture",
                "arcStep": "capture",
                "summary": "The route is still in the capture phase around keep it light.",
                "actionHint": "Keep one light route step around keep it light.",
                "recordedAt": recorded_at,
                "recentSignals": [
                    {
                        "signalType": "word_journal",
                        "route": "/vocabulary",
                        "label": "keep it light",
                        "summary": "The route has a fresh word journal signal.",
                        "recordedAt": recorded_at,
                    }
                ],
            }
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    plan = journey_service.get_today_plan(profile)
    refreshed_state = journey_repository.get_journey_state(profile.id)

    assert "carry it forward" in plan.summary.lower() or "reused keep it light once" in plan.summary.lower()
    assert refreshed_state is not None
    ritual_signal_memory = refreshed_state.strategy_snapshot.get("ritualSignalMemory")
    assert isinstance(ritual_signal_memory, dict)
    assert ritual_signal_memory.get("windowStage") == "reuse_in_route"
    assert ritual_signal_memory.get("arcStep") == "reuse"
    assert ritual_signal_memory.get("routeWindowStage") == "reuse_in_response"
    assert int(ritual_signal_memory.get("completedSinceCapture") or 0) >= 1


def test_completed_ritual_reuse_pass_updates_preview_and_persisted_window(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
        journey_repository,
    )
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="The route is ready for the next connected daily step.",
        next_best_action="Open the next route.",
        proof_lesson_handoff={},
        strategy_snapshot={},
        onboarding_completed_at=datetime.utcnow(),
    )
    journey_service.register_ritual_signal(
        profile=profile,
        signal_type="word_journal",
        route="/vocabulary",
        label="keep it light",
        summary="A fresh word journal phrase should come back into the next route before it goes cold.",
    )

    journey_repository.upsert_daily_loop_plan(
        user_id=profile.id,
        plan_date_key=datetime.utcnow().date().isoformat(),
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="vocabulary",
        headline="Keep the fresh phrase alive",
        summary="Bring the word journal capture back into one connected route.",
        why_this_now="The fresh phrase should land once in real output before it goes cold.",
        next_step_hint="Reuse keep it light once inside the route.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Word journal route",
        steps=[
            {
                "id": "warm-start",
                "skill": "coach",
                "title": "Warm start",
                "description": "Frame the route.",
                "durationMinutes": 2,
            }
        ],
    )
    lesson_run = journey_service.start_today_session(profile)
    assert lesson_run.lesson.blocks

    completed_run = lesson_runtime_repository.complete_lesson_run(
        profile.id,
        lesson_run.run_id,
        84,
        [
            BlockResultSubmission(
                block_id=lesson_run.lesson.blocks[0].id,
                user_response_type="text",
                user_response="I reused keep it light in a real example and kept the route connected.",
                feedback_summary="The ritual signal landed cleanly in the response.",
                score=84,
            )
        ],
    )
    assert completed_run is not None

    journey_service.register_completed_lesson(profile, completed_run)
    completed_state = journey_repository.get_journey_state(profile.id)

    assert completed_state is not None
    session_summary = completed_state.strategy_snapshot["sessionSummary"]
    ritual_evaluation = session_summary.get("ritualSignalEvaluation")
    assert isinstance(ritual_evaluation, dict)
    assert ritual_evaluation.get("nextWindowStage") == "reuse_in_route"
    assert ritual_evaluation.get("windowAction") == "advance_to_reuse"

    tomorrow_preview = completed_state.strategy_snapshot["tomorrowPreview"]
    assert tomorrow_preview.get("continuityMode") == "ritual_reuse"
    assert "keep it light" in str(tomorrow_preview.get("nextStepHint", "")).lower()

    persisted_ritual_memory = completed_state.strategy_snapshot.get("ritualSignalMemory")
    assert isinstance(persisted_ritual_memory, dict)
    assert persisted_ritual_memory.get("windowStage") == "reuse_in_route"
    assert persisted_ritual_memory.get("routeWindowStage") == "reuse_in_response"

    route_follow_up_memory = completed_state.strategy_snapshot.get("routeFollowUpMemory")
    assert isinstance(route_follow_up_memory, dict)
    assert route_follow_up_memory.get("currentRoute") == "/daily-loop"
    assert route_follow_up_memory.get("currentLabel") == "daily route"
    assert route_follow_up_memory.get("followUpRoute") == "/activity"
    assert route_follow_up_memory.get("followUpLabel") == "activity trail"
    assert route_follow_up_memory.get("carryRoute") == "/vocabulary"
    assert route_follow_up_memory.get("carryLabel") == "vocabulary support"
    assert route_follow_up_memory.get("stageLabel") == "Reuse in response"
    assert "keep it light" in str(route_follow_up_memory.get("summary") or "").lower()


def test_ready_to_carry_ritual_window_returns_guided_mix_to_broader_lesson(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    plan = DailyLoopPlan(
        id="plan-ready-to-carry",
        plan_date_key=datetime.utcnow().date().isoformat(),
        status="ready",
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="grammar",
        headline="Broader route day",
        summary="The route can widen again while the phrase stays available.",
        why_this_now="The ritual signal is ready to carry inside the broader route.",
        next_step_hint="Let the broader route lead again.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Broader route day",
        steps=[],
    )
    practice_mix = journey_service._build_route_practice_mix(  # noqa: SLF001
        profile=profile,
        plan=plan,
        module_rotation=[],
        weak_spots=[],
        due_vocabulary=[],
        continuity_seed=None,
        input_lane="reading",
        ritual_signal_memory={
            "activeSignalType": "word_journal",
            "activeRoute": "/vocabulary",
            "activeLabel": "keep it light",
            "recommendedFocus": "vocabulary",
            "windowDays": 1,
            "windowStage": "ready_to_carry",
            "arcStep": "carry",
            "summary": "The word journal signal is ready to carry forward inside the broader route.",
            "actionHint": "Let the broader route lead again while keep it light stays available.",
        },
    )
    assert isinstance(practice_mix, list) and practice_mix

    lesson_item = next((item for item in practice_mix if item.get("moduleKey") == "lesson"), None)
    vocabulary_item = next((item for item in practice_mix if item.get("moduleKey") == "vocabulary"), None)
    assert isinstance(lesson_item, dict)
    assert isinstance(vocabulary_item, dict)
    assert int(lesson_item.get("share") or 0) > int(vocabulary_item.get("share") or 0)
    assert "broader lesson flow" in str(lesson_item.get("reason") or "").lower()


def test_ritual_window_stage_reaches_route_context_and_daily_steps(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    plan = DailyLoopPlan(
        id="plan-ritual-window",
        plan_date_key=datetime.utcnow().date().isoformat(),
        status="ready",
        stage="daily_loop_ready",
        session_kind="recommended",
        focus_area="writing",
        headline="Connected reuse route",
        summary="Reuse the ritual signal directly inside the response lane.",
        why_this_now="The ritual window is now in connected reuse.",
        next_step_hint="Bring the ritual signal straight into one more response.",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        time_budget_minutes=profile.lesson_duration,
        estimated_minutes=20,
        recommended_lesson_type="mixed",
        recommended_lesson_title="Connected reuse route",
        steps=[],
    )
    ritual_signal_memory = {
        "activeSignalType": "word_journal",
        "activeRoute": "/vocabulary",
        "activeLabel": "keep it light",
        "recommendedFocus": "vocabulary",
        "windowDays": 1,
        "windowRemainingDays": 1,
        "windowStage": "reuse_in_route",
        "arcStep": "reuse",
        "routeWindowBias": "ritual_signal_window",
        "routeWindowStage": "reuse_in_response",
        "summary": "The route should reuse keep it light directly inside the response lane once more.",
        "actionHint": "Treat the next route as a connected reuse pass around keep it light.",
    }

    steps = journey_service._build_daily_steps(  # noqa: SLF001
        profile,
        plan.focus_area,
        plan.estimated_minutes,
        ritual_signal_memory=ritual_signal_memory,
    )
    assert any(step["title"] == "Connected ritual reuse" for step in steps)
    response_step = next((step for step in steps if step["id"] == "response"), None)
    assert isinstance(response_step, dict)
    assert "keep it light" in str(response_step.get("description") or "").lower()

    route_context = journey_service._build_guided_route_context(  # noqa: SLF001
        profile=profile,
        plan=plan,
        current_state=None,
        recommendation=None,
        weak_spots=[],
        due_vocabulary=[],
        continuity_seed=None,
    )
    route_context["ritualSignalMemory"] = ritual_signal_memory
    route_context["ritualSignalType"] = ritual_signal_memory["activeSignalType"]
    route_context["ritualSignalLabel"] = ritual_signal_memory["activeLabel"]
    route_context["ritualSignalStage"] = ritual_signal_memory["windowStage"]
    route_context["ritualSignalWindowStage"] = ritual_signal_memory["routeWindowStage"]
    route_context["ritualSignalWindowDays"] = ritual_signal_memory["windowDays"]
    route_context["ritualSignalWindowRemainingDays"] = ritual_signal_memory["windowRemainingDays"]
    route_context["ritualSignalSummary"] = ritual_signal_memory["summary"]

    lesson = lesson_repository.create_guided_route_template(
        profession_track=profile.profession_track,
        route_context=route_context,
        weak_spots=[],
        due_vocabulary=[],
    )
    assert lesson is not None
    response_block = next((block for block in lesson.blocks if isinstance(block.payload, dict)), None)
    assert response_block is not None
    block_route_context = response_block.payload.get("routeContext")
    assert isinstance(block_route_context, dict)
    assert block_route_context.get("ritualSignalWindowStage") == "reuse_in_response"



def test_speaking_and_writing_reviews_feed_shared_mistake_map(seeded_session_factory) -> None:
    content_repository = ContentRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    extraction_service = MistakeExtractionService()
    ai_orchestrator = AIOrchestrator(MockLLMProvider())

    speaking_service = SpeakingService(
        content_repository,
        ai_orchestrator,
        SpeakingAttemptRepository(seeded_session_factory),
        mistake_repository,
        VocabularyRepository(seeded_session_factory),
        extraction_service,
    )
    writing_service = WritingService(
        content_repository,
        ai_orchestrator,
        WritingAttemptRepository(seeded_session_factory),
        mistake_repository,
        VocabularyRepository(seeded_session_factory),
        extraction_service,
    )

    speaking_service.get_feedback(
        user_id="user-local-1",
        scenario_id="speaking-training-debrief",
        transcript="I goed to the workshop and work with this team since 2022.",
        feedback_language="ru",
        input_mode="text",
    )
    writing_service.review_draft(
        user_id="user-local-1",
        task_id="writing-reply-hiring-manager",
        draft="Hello team, people feels more confident and I goed to the client yesterday.",
        feedback_language="ru",
    )

    mistakes = mistake_repository.list_mistakes("user-local-1")
    weak_spots = mistake_repository.list_weak_spots("user-local-1", limit=5)

    irregular_past = next(mistake for mistake in mistakes if mistake.subtype == "irregular-past")
    assert irregular_past.repetition_count >= 2
    assert any(mistake.subtype == "subject-verb-agreement" for mistake in mistakes)
    assert any(spot.title == "Irregular Past Forms" for spot in weak_spots)

    vocabulary_items = VocabularyRepository(seeded_session_factory).list_due_items("user-local-1", limit=20)
    captured_words = {item.word.lower() for item in vocabulary_items}
    assert "went" in captured_words
    assert any(item.word.lower().startswith("i have") for item in vocabulary_items)
    assert any(item.source_module == "speaking" for item in vocabulary_items)
    assert any("Captured from repeated irregular past correction." == item.review_reason for item in vocabulary_items)
    assert any(item.linked_mistake_title == "Irregular Past Forms" for item in vocabulary_items)

    backlinks = VocabularyRepository(seeded_session_factory).list_mistake_backlinks("user-local-1", limit=10)
    assert any(link.weak_spot_title == "Irregular Past Forms" for link in backlinks)
    assert any("went" in link.example_words for link in backlinks)

    profile = ProfileRepository(seeded_session_factory).get_profile("user-local-1")
    assert profile is not None
    resolution_loop = AdaptiveStudyService(
        LessonRepository(seeded_session_factory),
        LessonRuntimeRepository(seeded_session_factory),
        RecommendationRepository(
            LessonRepository(seeded_session_factory),
            mistake_repository,
            VocabularyRepository(seeded_session_factory),
        ),
        mistake_repository,
        ProgressRepository(seeded_session_factory, LessonRepository(seeded_session_factory)),
        VocabularyRepository(seeded_session_factory),
    ).get_loop(profile)
    assert resolution_loop is not None
    assert any(item.weak_spot_title == "Irregular Past Forms" for item in resolution_loop.mistake_resolution)
    assert any(item.linked_vocabulary_count >= 1 for item in resolution_loop.mistake_resolution)
    assert resolution_loop.module_rotation
    assert resolution_loop.module_rotation[0].module_key != "lesson"


def test_recommendation_softens_when_weak_spots_are_recovering(seeded_session_factory) -> None:
    content_repository = ContentRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    extraction_service = MistakeExtractionService()
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        LessonRepository(seeded_session_factory),
        mistake_repository,
        vocabulary_repository,
        ProgressRepository(seeded_session_factory, LessonRepository(seeded_session_factory)),
    )
    ai_orchestrator = AIOrchestrator(MockLLMProvider())

    speaking_service = SpeakingService(
        content_repository,
        ai_orchestrator,
        SpeakingAttemptRepository(seeded_session_factory),
        mistake_repository,
        vocabulary_repository,
        extraction_service,
    )

    speaking_service.get_feedback(
        user_id="user-local-1",
        scenario_id="speaking-training-debrief",
        transcript="I work with this team since 2022 and I goed there yesterday.",
        feedback_language="ru",
        input_mode="text",
    )

    with seeded_session_factory() as session:
        stale_cutoff = datetime.utcnow() - timedelta(days=3)
        for subtype in ("tense-choice", "irregular-past"):
            model = session.query(MistakeRecord).filter(MistakeRecord.subtype == subtype).first()
            assert model is not None
            model.last_seen_at = stale_cutoff
        session.commit()

    profile = ProfileRepository(seeded_session_factory).get_profile("user-local-1")
    assert profile is not None

    recommendation = recommendation_repository.get_next_step(profile)
    assert recommendation is not None
    assert recommendation.lesson_type != "recovery"
    assert recommendation.focus_area == "pronunciation"
    assert any(
        phrase in recommendation.goal
        for phrase in (
            "Recovery pressure is easing",
            "recovery load is starting to soften",
            "repair no longer needs to dominate",
        )
    )
    assert any(
        phrase in recommendation.goal
        for phrase in (
            "weakest active skill",
            "learner model shows pronunciation under more pressure",
            "pronunciation needs the clearest support",
        )
    )

    adaptive_loop = AdaptiveStudyService(
        LessonRepository(seeded_session_factory),
        LessonRuntimeRepository(seeded_session_factory),
        recommendation_repository,
        mistake_repository,
        ProgressRepository(seeded_session_factory, LessonRepository(seeded_session_factory)),
        vocabulary_repository,
    ).get_loop(profile)
    assert adaptive_loop is not None
    assert adaptive_loop.module_rotation
    assert adaptive_loop.module_rotation[0].module_key != "lesson"


def test_recommendation_repository_prefers_connected_return_when_recovery_arc_exists(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
        journey_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    journey_repository.upsert_journey_state(
        user_id=profile.id,
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode=profile.onboarding_answers.preferred_mode,
        diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
        time_budget_minutes=profile.lesson_duration,
        current_focus_area="grammar",
        current_strategy_summary="The route should reopen through a protected connected return.",
        next_best_action="Start with a calmer connected route.",
        proof_lesson_handoff={},
        strategy_snapshot={
            "routeRecoveryMemory": {
                "phase": "protected_return",
                "horizonDays": 2,
                "focusSkill": "grammar",
                "supportPracticeTitle": "Speaking refresh",
                "sessionShape": "protected_mix",
                "summary": "The route is back in motion, but the next 2 sessions should still protect grammar before opening fully.",
                "actionHint": "Use a protected return for the next 2 routes and let the calmer support lane carry some of the load.",
                "nextPhaseHint": "If the return rhythm holds, the route can widen again after these protected sessions.",
            }
        },
        onboarding_completed_at=datetime.utcnow(),
    )

    recommendation = recommendation_repository.get_next_step(profile)

    assert recommendation is not None
    assert recommendation.lesson_type != "recovery"
    assert recommendation.focus_area == "grammar"
    assert "protected_return" in recommendation.goal.lower()


def test_goal_freshness_uses_different_templates_for_different_states() -> None:
    weak_spots = [
        WeakSpot(
            id="weak-1",
            title="Present Perfect vs Past Simple",
            category="grammar",
            recommendation="Review the tense contrast in context.",
        )
    ]
    resolution_map = {"Present Perfect vs Past Simple": "recovering"}

    softened_a = RecommendationRepository._build_softened_goal(
        base_goal="Return to the main track.",
        weak_spots=weak_spots,
        resolution_map=resolution_map,
        due_vocabulary_count=1,
        latest_lesson_type="recovery",
    )
    softened_b = RecommendationRepository._build_softened_goal(
        base_goal="Return to the main track.",
        weak_spots=weak_spots,
        resolution_map=resolution_map,
        due_vocabulary_count=3,
        latest_lesson_type="mixed",
    )

    recovery_a = RecommendationRepository._build_recovery_goal(
        weak_spots=weak_spots,
        priority_text="Present Perfect vs Past Simple (recovering)",
        due_vocabulary_count=1,
        latest_lesson_type="mixed",
        profession_track="trainer_skills",
    )
    recovery_b = RecommendationRepository._build_recovery_goal(
        weak_spots=weak_spots,
        priority_text="Present Perfect vs Past Simple (recovering)",
        due_vocabulary_count=2,
        latest_lesson_type="writing",
        profession_track="banking",
    )

    assert softened_a != softened_b
    assert recovery_a != recovery_b


def test_adaptive_generation_rationale_rotates_wording_with_state() -> None:
    weak_spots = [
        WeakSpot(
            id="weak-1",
            title="Present Perfect vs Past Simple",
            category="grammar",
            recommendation="Review the tense contrast in context.",
        )
    ]
    mistake_resolution = [
        MistakeResolutionSignal(
            weak_spot_title="Present Perfect vs Past Simple",
            weak_spot_category="grammar",
            status="recovering",
            repetition_count=2,
            last_seen_days_ago=3,
            linked_vocabulary_count=1,
            resolution_hint="The pattern is easing.",
        )
    ]

    rationale_a = AdaptiveStudyService._build_generation_rationale(
        recommendation_lesson_type="lesson",
        weak_spots=weak_spots,
        vocabulary_summary=VocabularyLoopSummary(
            due_count=1,
            new_count=0,
            active_count=3,
            mastered_count=2,
            weakest_category="grammar",
        ),
        listening_focus="audio_comprehension",
        mistake_resolution=mistake_resolution,
    )
    rationale_b = AdaptiveStudyService._build_generation_rationale(
        recommendation_lesson_type="lesson",
        weak_spots=weak_spots,
        vocabulary_summary=VocabularyLoopSummary(
            due_count=4,
            new_count=0,
            active_count=5,
            mastered_count=2,
            weakest_category="grammar",
        ),
        listening_focus="audio_comprehension",
        mistake_resolution=mistake_resolution,
    )

    assert rationale_a != rationale_b
    assert rationale_a[0] != rationale_b[0]


def test_adaptive_study_loop_and_vocabulary_review(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(lesson_repository, mistake_repository, vocabulary_repository)
    adaptive_service = AdaptiveStudyService(
        lesson_repository,
        lesson_runtime_repository,
        recommendation_repository,
        mistake_repository,
        progress_repository,
        vocabulary_repository,
    )

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    loop = adaptive_service.get_loop(profile)
    assert loop is not None
    assert loop.weak_spots
    assert loop.recommendation.title
    assert loop.due_vocabulary
    assert loop.vocabulary_backlinks
    assert loop.vocabulary_backlinks[0].weak_spot_title == "Feedback language for workshops"
    assert loop.mistake_resolution
    assert loop.module_rotation
    assert loop.module_rotation[0].module_key == "recovery"
    assert loop.vocabulary_summary.due_count >= 1
    assert loop.generation_rationale
    assert loop.listening_focus is not None

    reviewed = adaptive_service.review_vocabulary(profile.id, loop.due_vocabulary[0].id, successful=True)
    assert reviewed is not None
    assert reviewed.repetition_stage >= 2

    recovery_run = adaptive_service.start_recovery_run(profile)
    assert recovery_run.lesson.lesson_type == "recovery"
    assert recovery_run.lesson.blocks[0].block_type == "review_block"
    assert any(block.block_type == "summary_block" for block in recovery_run.lesson.blocks)
    assert any(block.block_type == "listening_block" for block in recovery_run.lesson.blocks)

    completed_recovery = lesson_runtime_repository.complete_lesson_run(
        profile.id,
        recovery_run.run_id,
        84,
        [],
    )
    assert completed_recovery is not None
    assert completed_recovery.lesson.lesson_type == "recovery"

    follow_up_recommendation = recommendation_repository.get_next_step(profile)
    assert follow_up_recommendation is not None
    assert follow_up_recommendation.lesson_type != "recovery"
    assert any(
        phrase in follow_up_recommendation.goal
        for phrase in (
            "Recovery loop completed",
            "focused repair pass is done",
            "Recovery work is finished for now",
        )
    )

    vocabulary_hub = adaptive_service.get_vocabulary_hub(profile.id)
    assert vocabulary_hub.summary.due_count >= 1
    assert vocabulary_hub.due_items
    assert vocabulary_hub.mistake_backlinks
    assert vocabulary_hub.mistake_backlinks[0].weak_spot_title == "Feedback language for workshops"


def test_listening_repository_builds_history_and_trends(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    diagnostic_service = DiagnosticService(
        LessonRepository(seeded_session_factory),
        lesson_runtime_repository,
        ProgressRepository(seeded_session_factory, LessonRepository(seeded_session_factory)),
        MistakeRepository(seeded_session_factory),
    )
    repository = ListeningRepository(seeded_session_factory)
    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    checkpoint_run = diagnostic_service.start_checkpoint_run(profile)
    listening_block = next(block for block in checkpoint_run.lesson.blocks if block.block_type == "listening_block")
    lesson_runtime_repository.complete_lesson_run(
        profile.id,
        checkpoint_run.run_id,
        76,
        [
            BlockResultSubmission(
                block_id=listening_block.id,
                user_response_type="text",
                user_response="The speaker updated the training deck and it was for new managers.",
                feedback_summary="Block completed. Transcript support was used for this listening block.",
                score=72,
            )
        ],
    )

    attempts = repository.list_attempts("user-local-1")
    trends = repository.get_trends("user-local-1")

    assert attempts
    assert attempts[0].block_title
    assert trends.recent_attempts >= 1


def test_diagnostic_roadmap_builds_level_path(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    diagnostic_service = DiagnosticService(lesson_repository, lesson_runtime_repository, progress_repository, mistake_repository)

    profile = profile_repository.get_profile("user-local-1")
    assert profile is not None

    roadmap = diagnostic_service.get_roadmap(profile)
    assert roadmap.target_level == "B2"
    assert roadmap.estimated_level in {"A2", "B1"}
    assert roadmap.milestones
    assert roadmap.milestones[0].level == "A2"
    assert len(roadmap.weakest_skills) >= 2

    checkpoint_run = diagnostic_service.start_checkpoint_run(profile)
    assert checkpoint_run.lesson.lesson_type == "diagnostic"
    listening_block = next(block for block in checkpoint_run.lesson.blocks if block.block_type == "listening_block")
    assert any(block.block_type == "pronunciation_block" for block in checkpoint_run.lesson.blocks)
    assert any(block.block_type == "writing_block" for block in checkpoint_run.lesson.blocks)
    assert "audio_variants" in listening_block.payload
    assert len(listening_block.payload["audio_variants"]) >= 2
