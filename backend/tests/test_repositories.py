from datetime import datetime, timedelta

from app.models.mistake_record import MistakeRecord
from app.repositories.content_repository import ContentRepository
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
from app.repositories.user_account_repository import UserAccountRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.repositories.writing_attempt_repository import WritingAttemptRepository
from app.providers.llm.mock_provider import MockLLMProvider
from app.services.adaptive_study_service.service import AdaptiveStudyService
from app.services.ai_orchestrator import AIOrchestrator
from app.services.diagnostic_service.service import DiagnosticService
from app.services.lesson_runtime_service.service import LessonRuntimeService
from app.services.mistake_extraction_service.service import MistakeExtractionService
from app.services.speaking_service.service import SpeakingService
from app.services.writing_service.service import WritingService
from app.schemas.lesson import BlockResultSubmission
from app.schemas.lesson import CompleteLessonRunRequest, StartLessonRunRequest
from app.schemas.feedback import AITextFeedback
from app.schemas.onboarding import CompleteOnboardingRequest
from app.schemas.provider import ProviderPreferenceUpdateRequest, ProviderType
from app.schemas.profile import OnboardingAnswers, ProfileUpdateRequest
from app.schemas.mistake import WeakSpot
from app.schemas.adaptive import MistakeResolutionSignal, VocabularyLoopSummary
from app.services.onboarding_service.service import OnboardingService
from app.services.profile_service.service import ProfileService


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
    assert any(
        phrase in recommendation.goal
        for phrase in (
            "Recovery pressure is easing",
            "recovery load is starting to soften",
            "repair no longer needs to dominate",
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
