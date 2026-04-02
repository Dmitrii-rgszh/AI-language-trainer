from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.models.lesson_template import LessonTemplate
from app.repositories.lesson_template_persistence import persist_lesson_template
from app.schemas.blueprint import FeedbackMode, LessonType


def create_diagnostic_template(
    session: Session,
    profession_track: str,
    current_level: str,
    target_level: str,
) -> LessonTemplate:
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
                                "acceptable_answers": ["new managers", "for new managers"],
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
                                "acceptable_answers": ["first-time facilitators", "facilitators"],
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
                                "acceptable_answers": ["junior coordinators", "for junior coordinators"],
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

    return persist_lesson_template(session, template, blocks)
