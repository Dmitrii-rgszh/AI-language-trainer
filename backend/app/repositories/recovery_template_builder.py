from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.models.lesson_template import LessonTemplate
from app.repositories.lesson_template_persistence import persist_lesson_template
from app.schemas.adaptive import VocabularyReviewItem
from app.schemas.blueprint import FeedbackMode, LessonType
from app.schemas.mistake import WeakSpot


def create_recovery_template(
    session: Session,
    profession_track: str,
    weak_spots: list[WeakSpot],
    due_vocabulary: list[VocabularyReviewItem],
    listening_focus: str | None = None,
) -> LessonTemplate:
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
        generation_rules=[
            "adaptive_recovery",
            focus_area,
            "due_vocabulary" if due_vocabulary else "no_due_vocabulary",
        ],
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

    return persist_lesson_template(session, template, blocks)
