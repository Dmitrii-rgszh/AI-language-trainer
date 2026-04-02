from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.lesson_run import LessonBlockRun, LessonRun
from app.models.lesson_template import LessonTemplate
from app.models.mistake_record import MistakeRecord
from app.models.progress_snapshot import ProgressSkillScore
from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel
from app.models.pronunciation_attempt import PronunciationAttempt
from app.models.vocabulary_item import VocabularyItem
from app.schemas.blueprint import (
    BlockRunStatus,
    LessonRunStatus,
    MistakeCategory,
    MistakeSeverity,
    UserResponseType,
    VocabularyStatus,
)
from app.schemas.profile import UserProfile

from .baselines import TRACK_BASELINES
from .constants import BASELINE_PREFIX
from .scoring import block_baseline, level_base, run_score, skill_score_map
from .selectors import (
    baseline_key,
    build_block_run_index,
    has_real_completed_run,
    has_real_mistakes,
    has_real_progress_snapshot,
    has_real_pronunciation_attempts,
    has_real_vocabulary,
    mistake_id,
    pick_legacy_or_bootstrap_run,
    select_template,
)
from .types import MistakeSpec, TrackBaselineSpec


class ProfileBootstrapService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def sync_profile_runtime(self, profile: UserProfile) -> None:
        spec = TRACK_BASELINES.get(profile.profession_track, TRACK_BASELINES["trainer_skills"])
        with self._session_factory() as session:
            template = select_template(session, profile.profession_track, spec["template_id"])
            if template is None:
                return

            profile_baseline_key = baseline_key(profile.id)
            lesson_run = None
            if not has_real_completed_run(session, profile.id):
                lesson_run = self._ensure_completed_run(
                    session, profile, template, spec, profile_baseline_key
                )

            block_run_ids = build_block_run_index(lesson_run)

            if not has_real_mistakes(session, profile.id):
                self._ensure_mistakes(session, profile, spec, profile_baseline_key, block_run_ids)

            if not has_real_progress_snapshot(session, profile.id):
                self._ensure_progress_snapshot(session, profile, lesson_run, profile_baseline_key)

            if not has_real_vocabulary(session, profile.id):
                self._ensure_vocabulary(session, profile, spec, profile_baseline_key)

            if not has_real_pronunciation_attempts(session, profile.id):
                self._ensure_pronunciation_attempt(session, profile, spec, profile_baseline_key)

            session.commit()

    def _ensure_completed_run(
        self,
        session: Session,
        profile: UserProfile,
        template: LessonTemplate,
        spec: TrackBaselineSpec,
        profile_baseline_key: str,
    ) -> LessonRun:
        run = pick_legacy_or_bootstrap_run(session, profile.id, profile_baseline_key)
        now = datetime.utcnow()
        started_at = now - timedelta(hours=2)
        completed_at = started_at + timedelta(minutes=profile.lesson_duration)

        if run is None:
            run = LessonRun(
                id=f"{BASELINE_PREFIX}run-{profile_baseline_key}",
                user_id=profile.id,
                template_id=template.id,
                status=LessonRunStatus.COMPLETED,
                recommended_by="profile_bootstrap",
                weak_spot_ids=[],
                started_at=started_at,
                completed_at=completed_at,
                score=run_score(profile),
            )
            session.add(run)
            session.flush()
        else:
            run.user_id = profile.id
            run.template_id = template.id
            run.status = LessonRunStatus.COMPLETED
            run.recommended_by = "profile_bootstrap"
            run.started_at = started_at
            run.completed_at = completed_at
            run.score = run_score(profile)

        run.weak_spot_ids = [
            mistake_id(profile_baseline_key, "grammar"),
            mistake_id(profile_baseline_key, "profession"),
        ]

        existing_block_runs = session.scalars(select(LessonBlockRun).where(LessonBlockRun.lesson_run_id == run.id)).all()
        for block_run in existing_block_runs:
            session.delete(block_run)
        session.flush()

        for index, block in enumerate(sorted(template.blocks, key=lambda item: item.position)):
            response_text, feedback_summary, score = block_baseline(block.block_type, spec)
            session.add(
                LessonBlockRun(
                    id=f"{BASELINE_PREFIX}block-run-{profile_baseline_key}-{index}",
                    lesson_run_id=run.id,
                    block_id=block.id,
                    status=BlockRunStatus.COMPLETED,
                    user_response_type=UserResponseType.TEXT,
                    user_response=response_text,
                    transcript=None,
                    feedback_summary=feedback_summary,
                    score=score,
                    started_at=started_at + timedelta(minutes=index * 3),
                    completed_at=started_at + timedelta(minutes=index * 3 + 2),
                )
            )

        session.flush()
        session.refresh(run)
        session.refresh(run, attribute_names=["block_runs", "template"])
        return run

    def _ensure_mistakes(
        self,
        session: Session,
        profile: UserProfile,
        spec: TrackBaselineSpec,
        profile_baseline_key: str,
        block_run_ids: dict[str, str],
    ) -> None:
        now = datetime.utcnow()
        self._upsert_mistake(
            session,
            profile,
            spec["grammar"],
            mistake_id(profile_baseline_key, "grammar"),
            "mistake-1",
            block_run_ids.get("grammar_block"),
            MistakeCategory.GRAMMAR,
            now - timedelta(days=8),
            now - timedelta(days=1),
        )
        self._upsert_mistake(
            session,
            profile,
            spec["profession"],
            mistake_id(profile_baseline_key, "profession"),
            "mistake-3",
            block_run_ids.get("profession_block"),
            MistakeCategory.PROFESSION,
            now - timedelta(days=7),
            now - timedelta(days=1),
        )

    def _upsert_mistake(
        self,
        session: Session,
        profile: UserProfile,
        mistake_spec: MistakeSpec,
        record_id: str,
        legacy_id: str,
        block_run_id: str | None,
        category: MistakeCategory,
        created_at: datetime,
        last_seen_at: datetime,
    ) -> None:
        legacy = session.get(MistakeRecord, legacy_id)
        record = legacy if legacy is not None and legacy.user_id == profile.id else session.get(MistakeRecord, record_id)
        if record is None:
            record = MistakeRecord(
                id=record_id,
                user_id=profile.id,
                category=category,
                subtype=mistake_spec["subtype"],
                source_module=mistake_spec["source_module"],
                source_block_run_id=block_run_id,
                original_text=mistake_spec["original_text"],
                corrected_text=mistake_spec["corrected_text"],
                explanation=mistake_spec["explanation"],
                severity=MistakeSeverity.MEDIUM,
                repetition_count=mistake_spec["repetition_count"],
                created_at=created_at,
                last_seen_at=last_seen_at,
            )
            session.add(record)
            return

        record.user_id = profile.id
        record.category = category
        record.subtype = mistake_spec["subtype"]
        record.source_module = mistake_spec["source_module"]
        record.source_block_run_id = block_run_id
        record.original_text = mistake_spec["original_text"]
        record.corrected_text = mistake_spec["corrected_text"]
        record.explanation = mistake_spec["explanation"]
        record.severity = MistakeSeverity.MEDIUM
        record.repetition_count = mistake_spec["repetition_count"]
        record.created_at = created_at
        record.last_seen_at = last_seen_at

    def _ensure_progress_snapshot(
        self,
        session: Session,
        profile: UserProfile,
        lesson_run: LessonRun | None,
        baseline_key: str,
    ) -> None:
        legacy = session.get(ProgressSnapshotModel, "snapshot-1")
        snapshot_id = f"{BASELINE_PREFIX}snapshot-{baseline_key}"
        snapshot = legacy if legacy is not None and legacy.user_id == profile.id else session.get(ProgressSnapshotModel, snapshot_id)
        if snapshot is None:
            snapshot = ProgressSnapshotModel(
                id=snapshot_id,
                user_id=profile.id,
                lesson_run_id=lesson_run.id if lesson_run else None,
                snapshot_date=date.today(),
                daily_goal_minutes=profile.lesson_duration,
                minutes_completed_today=max(10, min(180, profile.lesson_duration - 1)),
                streak=max(4, min(12, round((profile.speaking_priority + profile.grammar_priority + profile.profession_priority) / 2))),
            )
            session.add(snapshot)
        else:
            snapshot.user_id = profile.id
            snapshot.lesson_run_id = lesson_run.id if lesson_run else snapshot.lesson_run_id
            snapshot.snapshot_date = date.today()
            snapshot.daily_goal_minutes = profile.lesson_duration
            snapshot.minutes_completed_today = max(10, min(180, profile.lesson_duration - 1))
            snapshot.streak = max(4, min(12, round((profile.speaking_priority + profile.grammar_priority + profile.profession_priority) / 2)))

        snapshot.skill_scores = []
        for area, score in skill_score_map(profile).items():
            snapshot.skill_scores.append(
                ProgressSkillScore(
                    area=area,
                    score=score,
                    confidence=min(95, score + 16),
                    updated_at=datetime.utcnow(),
                )
            )

    def _ensure_vocabulary(
        self, session: Session, profile: UserProfile, spec: TrackBaselineSpec, baseline_key: str
    ) -> None:
        legacy_item = session.get(VocabularyItem, "vocab-1")
        for index, item_spec in enumerate(spec["vocabulary"]):
            item_id = f"{BASELINE_PREFIX}vocab-{baseline_key}-{item_spec['code']}"
            model = legacy_item if index == 0 and legacy_item is not None and legacy_item.user_id == profile.id else session.get(VocabularyItem, item_id)
            if model is None:
                model = VocabularyItem(
                    id=item_id,
                    user_id=profile.id,
                    word=item_spec["word"],
                    translation=item_spec["translation"],
                    context=item_spec["context"],
                    category=item_spec["category"],
                    source_module=item_spec["source_module"],
                    review_reason=item_spec["review_reason"],
                    linked_mistake_subtype=item_spec.get("linked_mistake_subtype"),
                    linked_mistake_title=item_spec.get("linked_mistake_title"),
                    learned_status=VocabularyStatus.ACTIVE,
                    repetition_stage=item_spec["repetition_stage"],
                    last_reviewed_at=datetime.utcnow() - timedelta(days=max(1, index)),
                )
                session.add(model)
                continue

            model.user_id = profile.id
            model.word = item_spec["word"]
            model.translation = item_spec["translation"]
            model.context = item_spec["context"]
            model.category = item_spec["category"]
            model.source_module = item_spec["source_module"]
            model.review_reason = item_spec["review_reason"]
            model.linked_mistake_subtype = item_spec.get("linked_mistake_subtype")
            model.linked_mistake_title = item_spec.get("linked_mistake_title")
            model.learned_status = VocabularyStatus.ACTIVE
            model.repetition_stage = item_spec["repetition_stage"]
            model.last_reviewed_at = datetime.utcnow() - timedelta(days=max(1, index))

    def _ensure_pronunciation_attempt(
        self,
        session: Session,
        profile: UserProfile,
        spec: TrackBaselineSpec,
        baseline_key: str,
    ) -> None:
        attempt_id = f"{BASELINE_PREFIX}pronunciation-{baseline_key}"
        pronunciation_spec = spec["pronunciation"]
        attempt = session.get(PronunciationAttempt, attempt_id)
        if attempt is None:
            attempt = PronunciationAttempt(
                id=attempt_id,
                user_id=profile.id,
                drill_id="pronunciation-soft-th-control",
                target_text=pronunciation_spec["target_text"],
                sound_focus="th",
                transcript=pronunciation_spec["transcript"],
                score=max(58, level_base(profile.current_level) + 6),
                feedback=pronunciation_spec["feedback"],
                weakest_words=list(pronunciation_spec["weakest_words"]),
                focus_issues=list(pronunciation_spec["focus_issues"]),
            )
            session.add(attempt)
            return

        attempt.user_id = profile.id
        attempt.drill_id = "pronunciation-soft-th-control"
        attempt.target_text = pronunciation_spec["target_text"]
        attempt.sound_focus = "th"
        attempt.transcript = pronunciation_spec["transcript"]
        attempt.score = max(58, level_base(profile.current_level) + 6)
        attempt.feedback = pronunciation_spec["feedback"]
        attempt.weakest_words = list(pronunciation_spec["weakest_words"])
        attempt.focus_issues = list(pronunciation_spec["focus_issues"])
