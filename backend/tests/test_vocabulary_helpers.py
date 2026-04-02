from datetime import datetime, timedelta

from app.models.vocabulary_item import VocabularyItem
from app.repositories.vocabulary_capture import build_capture
from app.repositories.vocabulary_mappers import build_mistake_backlinks, build_summary, is_due
from app.schemas.blueprint import MistakeCategory, MistakeSeverity, VocabularyStatus
from app.schemas.mistake_extraction import ExtractedMistake


def _build_vocab_item(
    *,
    item_id: str,
    word: str,
    category: str,
    linked_mistake_title: str | None = None,
    source_module: str = "speaking",
    learned_status: VocabularyStatus = VocabularyStatus.NEW,
    repetition_stage: int = 0,
    last_reviewed_at: datetime | None = None,
) -> VocabularyItem:
    return VocabularyItem(
        id=item_id,
        user_id="user-1",
        word=word,
        translation="translation",
        context="context",
        category=category,
        source_module=source_module,
        review_reason="reason",
        linked_mistake_subtype="tense-choice" if linked_mistake_title else None,
        linked_mistake_title=linked_mistake_title,
        learned_status=learned_status,
        repetition_stage=repetition_stage,
        last_reviewed_at=last_reviewed_at,
    )


def test_vocabulary_due_logic_and_summary() -> None:
    due_item = _build_vocab_item(
        item_id="v1",
        word="went",
        category="mistake_irregular_verbs",
        learned_status=VocabularyStatus.NEW,
    )
    mastered_fresh = _build_vocab_item(
        item_id="v2",
        word="have worked",
        category="mistake_tense_patterns",
        learned_status=VocabularyStatus.MASTERED,
        repetition_stage=6,
        last_reviewed_at=datetime.utcnow(),
    )

    assert is_due(due_item) is True
    assert is_due(mastered_fresh) is False

    summary = build_summary([due_item, mastered_fresh])
    assert summary.due_count == 1
    assert summary.new_count == 1
    assert summary.mastered_count == 1
    assert summary.weakest_category == "mistake_irregular_verbs"


def test_vocabulary_backlinks_group_and_rank_items() -> None:
    stale_time = datetime.utcnow() - timedelta(days=10)
    models = [
        _build_vocab_item(
            item_id="v1",
            word="went",
            category="mistake_irregular_verbs",
            linked_mistake_title="Irregular Past Forms",
            learned_status=VocabularyStatus.NEW,
        ),
        _build_vocab_item(
            item_id="v2",
            word="have worked",
            category="mistake_tense_patterns",
            linked_mistake_title="Present Perfect vs Past Simple",
            learned_status=VocabularyStatus.MASTERED,
            repetition_stage=5,
            last_reviewed_at=stale_time,
        ),
        _build_vocab_item(
            item_id="v3",
            word="went again",
            category="mistake_irregular_verbs",
            linked_mistake_title="Irregular Past Forms",
            source_module="writing",
            learned_status=VocabularyStatus.ACTIVE,
        ),
    ]

    backlinks = build_mistake_backlinks(models, limit=5)

    assert backlinks[0].weak_spot_title == "Irregular Past Forms"
    assert backlinks[0].due_count == 2
    assert "went" in backlinks[0].example_words
    assert set(backlinks[0].source_modules) == {"speaking", "writing"}


def test_build_capture_extracts_reusable_vocabulary_from_mistakes() -> None:
    irregular = build_capture(
        ExtractedMistake(
            category=MistakeCategory.GRAMMAR,
            subtype="irregular-past",
            source_module="speaking",
            original_text="I goed there yesterday.",
            corrected_text="I went there yesterday.",
            explanation="Use the irregular past form.",
            severity=MistakeSeverity.MEDIUM,
        )
    )
    tense = build_capture(
        ExtractedMistake(
            category=MistakeCategory.GRAMMAR,
            subtype="tense-choice",
            source_module="writing",
            original_text="I work with this team since 2022.",
            corrected_text="I have worked with this team since 2022.",
            explanation="Use Present Perfect with since.",
            severity=MistakeSeverity.MEDIUM,
        )
    )

    assert irregular is not None
    assert irregular["word"] == "went"
    assert irregular["linked_mistake_title"] == "Irregular Past Forms"
    assert tense is not None
    assert tense["word"].lower().startswith("i have worked")
    assert tense["linked_mistake_title"] == "Present Perfect vs Past Simple"
