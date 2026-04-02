from app.repositories.diagnostic_template_builder import create_diagnostic_template
from app.repositories.recovery_template_builder import create_recovery_template
from app.repositories.lesson_template_builders import (
    create_diagnostic_template as facade_create_diagnostic_template,
)
from app.repositories.lesson_template_builders import (
    create_recovery_template as facade_create_recovery_template,
)
from app.schemas.adaptive import VocabularyReviewItem
from app.schemas.mistake import WeakSpot


def test_lesson_template_builder_facade_reexports_domain_builders() -> None:
    assert facade_create_recovery_template is create_recovery_template
    assert facade_create_diagnostic_template is create_diagnostic_template


def test_recovery_template_builder_creates_expected_blocks(empty_session_factory) -> None:
    with empty_session_factory() as session:
        template = create_recovery_template(
            session=session,
            profession_track="trainer_skills",
            weak_spots=[
                WeakSpot(
                    id="weak-1",
                    title="Present Perfect vs Past Simple",
                    category="grammar",
                    recommendation="Review tense contrast.",
                )
            ],
            due_vocabulary=[
                VocabularyReviewItem(
                    id="vocab-1",
                    word="have worked",
                    translation="pattern",
                    context="I have worked here since 2022.",
                    category="mistake_tense_patterns",
                    source_module="speaking",
                    review_reason="reason",
                    linked_mistake_subtype="tense-choice",
                    linked_mistake_title="Present Perfect vs Past Simple",
                    learned_status="active",
                    repetition_stage=2,
                    due_now=True,
                )
            ],
            listening_focus="audio_comprehension",
        )

    block_types = [block.block_type for block in template.blocks]
    assert template.lesson_type.value == "recovery"
    assert "review_block" in block_types
    assert "vocab_block" in block_types
    assert "listening_block" in block_types
    assert block_types[-1] == "summary_block"


def test_diagnostic_template_builder_creates_checkpoint_structure(empty_session_factory) -> None:
    with empty_session_factory() as session:
        template = create_diagnostic_template(
            session=session,
            profession_track="trainer_skills",
            current_level="A2",
            target_level="B2",
        )

    block_types = [block.block_type for block in template.blocks]
    assert template.lesson_type.value == "diagnostic"
    assert block_types == [
        "grammar_block",
        "speaking_block",
        "listening_block",
        "pronunciation_block",
        "writing_block",
        "summary_block",
    ]
