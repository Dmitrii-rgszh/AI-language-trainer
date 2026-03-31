from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload, sessionmaker

from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.models.lesson_run import LessonRun
from app.models.lesson_template import LessonTemplate
from app.repositories.mappers import to_lesson, to_lesson_history_item, to_lesson_recommendation
from app.schemas.adaptive import VocabularyReviewItem
from app.schemas.blueprint import FeedbackMode, LessonType
from app.schemas.lesson import Lesson, LessonRecommendation
from app.schemas.mistake import WeakSpot
from app.schemas.progress import LessonHistoryItem


class LessonRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_recommended_lesson(self, profession_track: str | None = None) -> Lesson | None:
        with self._session_factory() as session:
            template = self._select_template(session, profession_track)
            return to_lesson(template) if template else None

    def get_recommendation(self, profession_track: str | None = None) -> LessonRecommendation | None:
        with self._session_factory() as session:
            template = self._select_template(session, profession_track)
            return to_lesson_recommendation(template) if template else None

    def list_recent_completed_lessons(self, user_id: str, limit: int = 10) -> list[LessonHistoryItem]:
        with self._session_factory() as session:
            statement = (
                select(LessonRun)
                .options(joinedload(LessonRun.template))
                .where(LessonRun.user_id == user_id, LessonRun.completed_at.is_not(None))
                .order_by(LessonRun.completed_at.desc())
                .limit(limit)
            )
            runs = session.scalars(statement).unique().all()
            return [to_lesson_history_item(run) for run in runs]

    def create_recovery_template(
        self,
        profession_track: str,
        weak_spots: list[WeakSpot],
        due_vocabulary: list[VocabularyReviewItem],
        listening_focus: str | None = None,
    ) -> LessonTemplate:
        with self._session_factory() as session:
            now = datetime.utcnow()
            template_id = f"template-recovery-{uuid4().hex[:10]}"
            primary_spot = weak_spots[0] if weak_spots else None
            focus_area = primary_spot.category if primary_spot else "speaking"
            focus_title = primary_spot.title if primary_spot else "Confidence rebuild"
            template = LessonTemplate(
                id=template_id,
                lesson_type=LessonType.RECOVERY,
                title=f"Recovery Loop: {focus_title}",
                goal="Закрыть повторяющиеся ошибки, повторить ключевую лексику и вернуться в основной lesson flow.",
                difficulty="A2-B2 adaptive",
                estimated_duration=18 if not due_vocabulary else 22,
                enabled_tracks=[profession_track],
                generation_rules=["adaptive_recovery", focus_area, "due_vocabulary" if due_vocabulary else "no_due_vocabulary"],
                created_at=now,
                updated_at=now,
            )
            session.add(template)
            session.flush()

            blocks: list[LessonBlockModel] = [
                LessonBlockModel(
                    id=f"block-recovery-review-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=0,
                    block_type="review_block",
                    title="Recovery review",
                    instructions="Посмотри на повторяющиеся ошибки и проговори правильные паттерны перед новым ответом.",
                    estimated_minutes=4,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[],
                    payload={
                        "source_mistake_ids": [spot.id for spot in weak_spots],
                        "review_items": [spot.title for spot in weak_spots],
                        "target_error_types": [spot.category for spot in weak_spots],
                    },
                )
            ]

            if due_vocabulary:
                blocks.append(
                    LessonBlockModel(
                        id=f"block-recovery-vocab-{uuid4().hex[:10]}",
                        lesson_template_id=template.id,
                        position=len(blocks),
                        block_type="vocab_block",
                        title="Vocabulary refresh",
                        instructions="Вспомни перевод, контекст и собери по одной своей фразе на каждое слово.",
                        estimated_minutes=5,
                        feedback_mode=FeedbackMode.AFTER_BLOCK,
                        depends_on_block_ids=[blocks[0].id],
                        payload={
                            "lexical_set": "adaptive_recovery",
                            "vocabulary_ids": [item.id for item in due_vocabulary],
                            "phrases": [item.context for item in due_vocabulary],
                        },
                    )
                )

            middle_block_type = "grammar_block" if focus_area == "grammar" else "speaking_block"
            middle_payload = (
                {
                    "topic_id": primary_spot.id if primary_spot else "adaptive-grammar",
                    "focus_points": [spot.title for spot in weak_spots] or ["repair core pattern"],
                    "prompts": [
                        "Rewrite the incorrect pattern into two correct examples.",
                        "Give one new work-related sentence using the corrected form.",
                    ],
                    "target_error_types": [spot.category for spot in weak_spots],
                }
                if middle_block_type == "grammar_block"
                else {
                    "scenario_id": "adaptive-recovery-speaking",
                    "mode": "guided",
                    "prompts": [
                        "Give a short update using the corrected pattern from the review block.",
                        "Use at least one vocabulary item from the repetition queue if possible.",
                    ],
                    "expects_voice": False,
                    "feedback_focus": [spot.title for spot in weak_spots] or ["clarity", "accuracy"],
                }
            )
            blocks.append(
                LessonBlockModel(
                    id=f"block-recovery-core-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=len(blocks),
                    block_type=middle_block_type,
                    title="Recovery drill",
                    instructions="Собери короткий, но точный ответ без повторения недавней ошибки.",
                    estimated_minutes=8,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[blocks[-1].id] if blocks else [],
                    payload=middle_payload,
                )
            )

            if listening_focus:
                blocks.append(
                    LessonBlockModel(
                        id=f"block-recovery-listening-{uuid4().hex[:10]}",
                        lesson_template_id=template.id,
                        position=len(blocks),
                        block_type="listening_block",
                        title="Listening recovery check",
                        instructions="Прослушай короткий рабочий апдейт и ответь без transcript, чтобы закрепить listening under pressure.",
                        estimated_minutes=4,
                        feedback_mode=FeedbackMode.AFTER_BLOCK,
                        depends_on_block_ids=[blocks[-1].id],
                        payload={
                            "audio_variants": [
                                {
                                    "id": "recovery-listening-1",
                                    "label": "Workshop update",
                                    "transcript": "I updated the session outline, shortened the icebreaker, and added one example for new facilitators.",
                                    "questions": [
                                        {
                                            "prompt": "What changed in the session plan?",
                                            "acceptable_answers": [
                                                "updated the session outline",
                                                "shortened the icebreaker",
                                            ],
                                        },
                                        {
                                            "prompt": "Who is the new example for?",
                                            "acceptable_answers": ["new facilitators", "facilitators"],
                                        },
                                    ],
                                }
                            ],
                            "focus_area": listening_focus,
                            "answer_key": ["session outline", "icebreaker", "new facilitators"],
                            "slow_mode_allowed": True,
                        },
                    )
                )

            blocks.append(
                LessonBlockModel(
                    id=f"block-recovery-summary-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=len(blocks),
                    block_type="summary_block",
                    title="Recovery wrap-up",
                    instructions="Зафиксируй одно исправленное правило, одно слово и один следующий шаг.",
                    estimated_minutes=3,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[blocks[-1].id],
                    payload={
                        "recap_prompts": [
                            "What pattern did you fix?",
                            "Which word from review should stay active tomorrow?",
                        ],
                        "next_step": "Return to the main lesson flow after this recovery session.",
                        "save_to_progress": True,
                    },
                )
            )

            session.add_all(blocks)
            session.commit()
            session.refresh(template)
            session.refresh(template, attribute_names=["blocks"])
            return template

    def create_diagnostic_template(
        self,
        profession_track: str,
        current_level: str,
        target_level: str,
    ) -> LessonTemplate:
        with self._session_factory() as session:
            now = datetime.utcnow()
            template_id = f"template-diagnostic-{uuid4().hex[:10]}"
            template = LessonTemplate(
                id=template_id,
                lesson_type=LessonType.DIAGNOSTIC,
                title=f"Checkpoint Diagnostic: {current_level} -> {target_level}",
                goal="Проверить контроль по grammar, speaking, listening и writing, чтобы обновить долгую roadmap-траекторию.",
                difficulty=f"{current_level}-{target_level}",
                estimated_duration=24,
                enabled_tracks=[profession_track],
                generation_rules=["diagnostic_checkpoint", current_level, target_level],
                created_at=now,
                updated_at=now,
            )
            session.add(template)
            session.flush()

            blocks = [
                LessonBlockModel(
                    id=f"block-diagnostic-grammar-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=0,
                    block_type="grammar_block",
                    title="Grammar checkpoint",
                    instructions="Ответь коротко и точно, как если бы это был мини-тест на рабочую грамматику.",
                    estimated_minutes=5,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[],
                    payload={
                        "topic_id": "diagnostic-grammar",
                        "focus_points": ["tense control", "sentence accuracy", "professional updates"],
                        "prompts": [
                            "Write two correct sentences about work you have done since last month.",
                            "Rewrite one incorrect sentence into a correct professional version.",
                        ],
                        "target_error_types": ["grammar"],
                    },
                ),
                LessonBlockModel(
                    id=f"block-diagnostic-speaking-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=1,
                    block_type="speaking_block",
                    title="Speaking checkpoint",
                    instructions="Дай короткий structured answer as if you were speaking to a colleague or learner.",
                    estimated_minutes=5,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[],
                    payload={
                        "scenario_id": "diagnostic-speaking-checkpoint",
                        "mode": "guided",
                        "prompts": [
                            "Summarize your recent progress and your next learning step in English.",
                            "Explain one challenge you still have and how you plan to fix it.",
                        ],
                        "expects_voice": False,
                        "feedback_focus": ["clarity", "tense control", "structure"],
                    },
                ),
                LessonBlockModel(
                    id=f"block-diagnostic-listening-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=2,
                    block_type="listening_block",
                    title="Listening checkpoint",
                    instructions="Прослушай аудио-промпт и ответь на вопросы без опоры на transcript, если можешь.",
                    estimated_minutes=4,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[],
                    payload={
                        "audio_asset_id": "diagnostic-transcript-1",
                        "transcript": "Hello team, I have updated the training deck, simplified the onboarding section, and added two practical examples for new managers.",
                        "audio_variants": [
                            {
                                "id": "listening-variant-deck",
                                "label": "Team update",
                                "transcript": "Hello team, I have updated the training deck, simplified the onboarding section, and added two practical examples for new managers.",
                                "questions": [
                                    {
                                        "prompt": "What did the speaker update?",
                                        "acceptable_answers": [
                                            "training deck",
                                            "updated the training deck",
                                            "onboarding section",
                                            "simplified the onboarding section",
                                        ],
                                    },
                                    {
                                        "prompt": "Who are the new examples for?",
                                        "acceptable_answers": [
                                            "new managers",
                                            "for new managers",
                                        ],
                                    },
                                ],
                            },
                            {
                                "id": "listening-variant-workshop",
                                "label": "Workshop recap",
                                "transcript": "Hi everyone, I finished the workshop outline, shortened the opening activity, and prepared a new checklist for first-time facilitators.",
                                "questions": [
                                    {
                                        "prompt": "What was completed or changed?",
                                        "acceptable_answers": [
                                            "workshop outline",
                                            "finished the workshop outline",
                                            "shortened the opening activity",
                                            "opening activity",
                                        ],
                                    },
                                    {
                                        "prompt": "Who is the new checklist for?",
                                        "acceptable_answers": [
                                            "first-time facilitators",
                                            "facilitators",
                                        ],
                                    },
                                ],
                            },
                            {
                                "id": "listening-variant-report",
                                "label": "Project report",
                                "transcript": "Good morning, I revised the weekly report, clarified the budget notes, and added a short action list for junior coordinators.",
                                "questions": [
                                    {
                                        "prompt": "What did the speaker revise or clarify?",
                                        "acceptable_answers": [
                                            "weekly report",
                                            "revised the weekly report",
                                            "budget notes",
                                            "clarified the budget notes",
                                        ],
                                    },
                                    {
                                        "prompt": "Who is the action list for?",
                                        "acceptable_answers": [
                                            "junior coordinators",
                                            "for junior coordinators",
                                        ],
                                    },
                                ],
                            },
                        ],
                        "questions": [
                            "What did the speaker update or change?",
                            "Who is the new material for?",
                        ],
                        "answer_key": [
                            "training deck",
                            "onboarding section",
                            "new managers",
                            "workshop outline",
                            "opening activity",
                            "first-time facilitators",
                            "weekly report",
                            "budget notes",
                            "junior coordinators",
                        ],
                        "slow_mode_allowed": True,
                    },
                ),
                LessonBlockModel(
                    id=f"block-diagnostic-pronunciation-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=3,
                    block_type="pronunciation_block",
                    title="Pronunciation checkpoint",
                    instructions="Прослушай фразу, запиши свой вариант и проверь, насколько система распознала ключевые слова.",
                    estimated_minutes=4,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[],
                    payload={
                        "sound_focus": ["th", "sentence stress"],
                        "phrase_drills": [
                            "thank the team for the thoughtful feedback",
                            "three trainers shared their progress",
                        ],
                        "minimal_pairs": ["think/sink", "three/free"],
                        "shadowing_script": "thank the team for the thoughtful feedback",
                    },
                ),
                LessonBlockModel(
                    id=f"block-diagnostic-writing-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=4,
                    block_type="writing_block",
                    title="Writing checkpoint",
                    instructions="Напиши короткий professional reply with clear structure and tone control.",
                    estimated_minutes=4,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[],
                    payload={
                        "task_id": "diagnostic-writing-checkpoint",
                        "brief": "Reply to a teammate, confirm progress, mention one difficulty, and suggest a next step.",
                        "checklist": ["clarity", "professional tone", "grammar accuracy"],
                        "tone": "professional and clear",
                    },
                ),
                LessonBlockModel(
                    id=f"block-diagnostic-summary-{uuid4().hex[:10]}",
                    lesson_template_id=template.id,
                    position=5,
                    block_type="summary_block",
                    title="Checkpoint summary",
                    instructions="Зафиксируй, какой навык оказался сильнее всего и что ещё нужно подтянуть до следующего уровня.",
                    estimated_minutes=2,
                    feedback_mode=FeedbackMode.AFTER_BLOCK,
                    depends_on_block_ids=[],
                    payload={
                        "recap_prompts": [
                            "Which skill felt strongest?",
                            "Which skill needs the next focused cycle?",
                        ],
                        "next_step": "Use the refreshed roadmap to choose the next adaptive lesson.",
                        "save_to_progress": True,
                    },
                ),
            ]

            session.add_all(blocks)
            session.commit()
            session.refresh(template)
            session.refresh(template, attribute_names=["blocks"])
            return template

    @staticmethod
    def _select_template(session: Session, profession_track: str | None = None) -> LessonTemplate | None:
        statement = (
            select(LessonTemplate)
            .options(selectinload(LessonTemplate.blocks))
            .order_by(LessonTemplate.created_at.asc())
        )
        templates = session.scalars(statement).unique().all()
        if not templates:
            return None

        if profession_track:
            matching = next(
                (template for template in templates if profession_track in (template.enabled_tracks or [])),
                None,
            )
            if matching:
                return matching

        return templates[0]
