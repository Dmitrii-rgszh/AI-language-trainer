from __future__ import annotations

from datetime import date, datetime, timedelta
from hashlib import sha1

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
    SkillArea,
    UserResponseType,
    VocabularyStatus,
)
from app.schemas.profile import UserProfile


BASELINE_PREFIX = "bootstrap-"
LEGACY_LESSON_RUN_IDS = {"run-1"}
LEGACY_MISTAKE_IDS = {"mistake-1", "mistake-3"}
LEGACY_PROGRESS_IDS = {"snapshot-1"}
LEGACY_VOCAB_IDS = {"vocab-1"}

LEVEL_BASE_SCORES = {
    "A1": 34,
    "A2": 46,
    "B1": 58,
    "B2": 71,
    "C1": 82,
    "C2": 91,
}

TRACK_SCORE_ADJUSTMENTS = {
    "trainer_skills": {
        SkillArea.GRAMMAR: 2,
        SkillArea.SPEAKING: 4,
        SkillArea.LISTENING: 0,
        SkillArea.PRONUNCIATION: 1,
        SkillArea.WRITING: 1,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 0,
    },
    "insurance": {
        SkillArea.GRAMMAR: 2,
        SkillArea.SPEAKING: 2,
        SkillArea.LISTENING: 3,
        SkillArea.PRONUNCIATION: 0,
        SkillArea.WRITING: 1,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 2,
    },
    "banking": {
        SkillArea.GRAMMAR: 2,
        SkillArea.SPEAKING: 2,
        SkillArea.LISTENING: 2,
        SkillArea.PRONUNCIATION: 0,
        SkillArea.WRITING: 2,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 1,
    },
    "ai_business": {
        SkillArea.GRAMMAR: 3,
        SkillArea.SPEAKING: 2,
        SkillArea.LISTENING: 1,
        SkillArea.PRONUNCIATION: 0,
        SkillArea.WRITING: 3,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 0,
    },
    "cross_cultural": {
        SkillArea.GRAMMAR: 1,
        SkillArea.SPEAKING: 4,
        SkillArea.LISTENING: 2,
        SkillArea.PRONUNCIATION: 1,
        SkillArea.WRITING: 0,
        SkillArea.PROFESSION_ENGLISH: 1,
        SkillArea.REGULATION_EU: 0,
    },
}

TRACK_BASELINES = {
    "trainer_skills": {
        "template_id": "template-trainer-daily-flow",
        "grammar": {
            "subtype": "tense-choice",
            "source_module": "speaking",
            "original_text": "I work with this team since 2022.",
            "corrected_text": "I have worked with this team since 2022.",
            "explanation": "Нужен Present Perfect, потому что действие началось в прошлом и продолжается сейчас.",
            "repetition_count": 4,
        },
        "profession": {
            "subtype": "feedback-language",
            "source_module": "profession",
            "original_text": "This part is wrong.",
            "corrected_text": "This part could be clearer for the audience.",
            "explanation": "Для trainer context лучше использовать мягкие формулировки.",
            "repetition_count": 3,
        },
        "vocabulary": [
            {
                "code": "stakeholder",
                "word": "stakeholder",
                "translation": "заинтересованная сторона",
                "context": "Our stakeholders have asked for a shorter training format.",
                "category": "trainer_skills",
                "source_module": "profession",
                "review_reason": "Core trainer vocabulary to keep active in workshop updates.",
                "linked_mistake_subtype": "feedback-language",
                "linked_mistake_title": "Feedback language for workshops",
                "repetition_stage": 2,
            },
            {
                "code": "facilitation",
                "word": "facilitation",
                "translation": "фасилитация",
                "context": "Clear facilitation language keeps the workshop calm and structured.",
                "category": "trainer_skills",
                "source_module": "profession",
                "review_reason": "Useful trainer vocabulary for debrief and workshop structure.",
                "repetition_stage": 1,
            },
            {
                "code": "debrief",
                "word": "debrief",
                "translation": "разбор после сессии",
                "context": "We scheduled a short debrief after the session.",
                "category": "trainer_skills",
                "source_module": "speaking",
                "review_reason": "High-frequency workshop follow-up phrase.",
                "repetition_stage": 1,
            },
        ],
        "speaking_response": "I have improved the workshop opening, and I have added clearer examples for new managers.",
        "summary_response": "I need to keep Present Perfect active and use softer feedback after each training session.",
        "pronunciation": {
            "target_text": "thank the team for the thoughtful feedback",
            "transcript": "tank the team for the thoughtful feedback",
            "feedback": "The rhythm is stable, but /th/ still softens at the start of key words.",
            "weakest_words": ["thank", "thoughtful"],
            "focus_issues": ["/th/"],
        },
    },
    "insurance": {
        "template_id": "template-insurance-client-flow",
        "grammar": {
            "subtype": "future-form-choice",
            "source_module": "grammar",
            "original_text": "Tomorrow I discuss the coverage options with the client.",
            "corrected_text": "Tomorrow I am going to discuss the coverage options with the client.",
            "explanation": "Для запланированного следующего шага здесь лучше использовать future form с going to.",
            "repetition_count": 3,
        },
        "profession": {
            "subtype": "client-needs-language",
            "source_module": "profession",
            "original_text": "You need this policy because it is better.",
            "corrected_text": "Could we look at the protection options that fit your current needs?",
            "explanation": "В insurance dialogue лучше сначала уточнять потребность и мягко предлагать вариант.",
            "repetition_count": 3,
        },
        "vocabulary": [
            {
                "code": "coverage",
                "word": "coverage",
                "translation": "страховое покрытие",
                "context": "We reviewed the coverage options before the next client call.",
                "category": "insurance",
                "source_module": "profession",
                "review_reason": "Core client-facing insurance vocabulary.",
                "linked_mistake_subtype": "client-needs-language",
                "linked_mistake_title": "Client needs analysis language",
                "repetition_stage": 2,
            },
            {
                "code": "premium",
                "word": "premium",
                "translation": "страховая премия",
                "context": "The client asked how the premium could change next year.",
                "category": "insurance",
                "source_module": "profession",
                "review_reason": "Useful for follow-up explanations after needs analysis.",
                "repetition_stage": 1,
            },
            {
                "code": "claim",
                "word": "claim",
                "translation": "страховой случай / претензия",
                "context": "I explained what documents are needed for a claim.",
                "category": "insurance",
                "source_module": "speaking",
                "review_reason": "High-frequency insurance support term.",
                "repetition_stage": 1,
            },
        ],
        "speaking_response": "We are going to review the client's protection needs and send a short follow-up summary after the call.",
        "summary_response": "I need cleaner next-step language and softer phrasing when I explain protection options.",
        "pronunciation": {
            "target_text": "three thoughtful themes for client protection",
            "transcript": "free thoughtful themes for client protection",
            "feedback": "The sentence is understandable, but /th/ still shifts toward /f/ in the opening phrase.",
            "weakest_words": ["three", "themes"],
            "focus_issues": ["/th/"],
        },
    },
    "banking": {
        "template_id": "template-banking-client-flow",
        "grammar": {
            "subtype": "tense-choice",
            "source_module": "speaking",
            "original_text": "I checked the transfer today and I sent the update now.",
            "corrected_text": "I have checked the transfer today and I have already sent the update.",
            "explanation": "Когда важен текущий результат банковского апдейта, нужен Present Perfect.",
            "repetition_count": 3,
        },
        "profession": {
            "subtype": "banking-clarity-language",
            "source_module": "profession",
            "original_text": "This fee is normal, so just use this option.",
            "corrected_text": "Let me explain the fee difference and show which option fits this transfer better.",
            "explanation": "В banking English лучше объяснять выбор и benefit, а не давать резкое указание.",
            "repetition_count": 3,
        },
        "vocabulary": [
            {
                "code": "transfer",
                "word": "transfer",
                "translation": "перевод",
                "context": "I checked the transfer status before calling the client back.",
                "category": "banking",
                "source_module": "profession",
                "review_reason": "Core banking support vocabulary.",
                "linked_mistake_subtype": "banking-clarity-language",
                "linked_mistake_title": "Banking product clarity",
                "repetition_stage": 2,
            },
            {
                "code": "statement",
                "word": "statement",
                "translation": "выписка",
                "context": "The client asked how to read the latest statement.",
                "category": "banking",
                "source_module": "profession",
                "review_reason": "Common banking explanation term.",
                "repetition_stage": 1,
            },
            {
                "code": "fee",
                "word": "fee",
                "translation": "комиссия",
                "context": "I explained the fee difference in a calmer way.",
                "category": "banking",
                "source_module": "speaking",
                "review_reason": "Useful for product and payment explanations.",
                "repetition_stage": 1,
            },
        ],
        "speaking_response": "I have checked the payment status, and I can explain the next transfer step in a simpler way now.",
        "summary_response": "I need clearer client-friendly phrases when I explain transfer options and fees.",
        "pronunciation": {
            "target_text": "thank the client and clarify the transfer",
            "transcript": "tank the client and clarify the transfer",
            "feedback": "The main idea is clear, but the opening /th/ still drops too quickly.",
            "weakest_words": ["thank"],
            "focus_issues": ["/th/"],
        },
    },
    "ai_business": {
        "template_id": "template-ai-business-flow",
        "grammar": {
            "subtype": "tense-choice",
            "source_module": "writing",
            "original_text": "We tested the workflow this week and now it saves time for the team.",
            "corrected_text": "We have tested the workflow this week, and now it saves time for the team.",
            "explanation": "Для недавнего AI experiment с актуальным результатом здесь лучше подходит Present Perfect.",
            "repetition_count": 3,
        },
        "profession": {
            "subtype": "risk-aware-language",
            "source_module": "profession",
            "original_text": "The AI tool is safe, so we can automate everything.",
            "corrected_text": "The AI tool helps with the draft, but we still need a human review step.",
            "explanation": "Для business AI communication важно оставлять guardrails и human review в формулировке.",
            "repetition_count": 3,
        },
        "vocabulary": [
            {
                "code": "workflow",
                "word": "workflow",
                "translation": "рабочий процесс",
                "context": "We have improved the workflow after the latest review cycle.",
                "category": "ai_business",
                "source_module": "profession",
                "review_reason": "Core AI business explanation term.",
                "linked_mistake_subtype": "risk-aware-language",
                "linked_mistake_title": "Risk-aware AI explanations",
                "repetition_stage": 2,
            },
            {
                "code": "guardrail",
                "word": "guardrail",
                "translation": "ограничитель / safeguard",
                "context": "This guardrail keeps the AI draft inside the approved workflow.",
                "category": "ai_business",
                "source_module": "profession",
                "review_reason": "Important for safe AI process language.",
                "repetition_stage": 1,
            },
            {
                "code": "approval",
                "word": "approval",
                "translation": "согласование",
                "context": "We still need an approval step before the final send.",
                "category": "ai_business",
                "source_module": "writing",
                "review_reason": "Useful in AI implementation updates and process notes.",
                "repetition_stage": 1,
            },
        ],
        "speaking_response": "We have tested the workflow, and we still keep a human review step before the final output.",
        "summary_response": "I need risk-aware wording so the AI update sounds useful, practical, and safe for business.",
        "pronunciation": {
            "target_text": "this workflow still needs a thoughtful review",
            "transcript": "dis workflow still needs a thoughtful review",
            "feedback": "The message is clear, but /th/ and sentence stress still need a cleaner contrast.",
            "weakest_words": ["this", "thoughtful"],
            "focus_issues": ["/th/", "sentence stress"],
        },
    },
    "cross_cultural": {
        "template_id": "template-cross-cultural-daily-flow",
        "grammar": {
            "subtype": "tense-choice",
            "source_module": "speaking",
            "original_text": "I already try this route before.",
            "corrected_text": "I have already tried this route before.",
            "explanation": "Для недавнего опыта и результата в настоящем здесь лучше подходит Present Perfect.",
            "repetition_count": 3,
        },
        "profession": {
            "subtype": "conversation-flow-language",
            "source_module": "profession",
            "original_text": "Tell me where is the station.",
            "corrected_text": "Could you tell me where the station is, please?",
            "explanation": "Для everyday conversation лучше использовать более вежливый и естественный вопрос.",
            "repetition_count": 3,
        },
        "vocabulary": [
            {
                "code": "direction",
                "word": "direction",
                "translation": "направление / маршрут",
                "context": "I asked for directions before the next stop.",
                "category": "cross_cultural",
                "source_module": "profession",
                "review_reason": "Useful everyday vocabulary for travel and daily communication.",
                "linked_mistake_subtype": "conversation-flow-language",
                "linked_mistake_title": "Everyday conversation flow",
                "repetition_stage": 2,
            },
            {
                "code": "schedule",
                "word": "schedule",
                "translation": "расписание / план",
                "context": "We checked the schedule before the next visit.",
                "category": "cross_cultural",
                "source_module": "speaking",
                "review_reason": "Helpful for everyday planning and school-friendly communication.",
                "repetition_stage": 1,
            },
            {
                "code": "question",
                "word": "question",
                "translation": "вопрос",
                "context": "I asked one more question to keep the conversation going.",
                "category": "cross_cultural",
                "source_module": "speaking",
                "review_reason": "High-frequency word for daily interaction practice.",
                "repetition_stage": 1,
            },
        ],
        "speaking_response": "I have practiced a few useful phrases, and I can ask a clearer question now.",
        "summary_response": "I need to keep polite questions and simple recent-update sentences active in daily English.",
        "pronunciation": {
            "target_text": "thank them for the thoughtful directions",
            "transcript": "tank them for the thoughtful directions",
            "feedback": "The sentence is easy to follow, but /th/ still needs a cleaner start in common everyday phrases.",
            "weakest_words": ["thank", "thoughtful"],
            "focus_issues": ["/th/"],
        },
    },
}


class ProfileBootstrapService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def sync_profile_runtime(self, profile: UserProfile) -> None:
        spec = TRACK_BASELINES.get(profile.profession_track, TRACK_BASELINES["trainer_skills"])
        with self._session_factory() as session:
            template = self._select_template(session, profile.profession_track, spec["template_id"])
            if template is None:
                return

            baseline_key = self._baseline_key(profile.id)
            lesson_run = None
            if not self._has_real_completed_run(session, profile.id):
                lesson_run = self._ensure_completed_run(session, profile, template, spec, baseline_key)

            block_run_ids = self._build_block_run_index(lesson_run)

            if not self._has_real_mistakes(session, profile.id):
                self._ensure_mistakes(session, profile, spec, baseline_key, block_run_ids)

            if not self._has_real_progress_snapshot(session, profile.id):
                self._ensure_progress_snapshot(session, profile, lesson_run, baseline_key)

            if not self._has_real_vocabulary(session, profile.id):
                self._ensure_vocabulary(session, profile, spec, baseline_key)

            if not self._has_real_pronunciation_attempts(session, profile.id):
                self._ensure_pronunciation_attempt(session, profile, spec, baseline_key)

            session.commit()

    @staticmethod
    def _baseline_key(user_id: str) -> str:
        return sha1(user_id.encode("utf-8")).hexdigest()[:10]

    @staticmethod
    def _is_bootstrap_id(value: str, legacy_ids: set[str]) -> bool:
        return value.startswith(BASELINE_PREFIX) or value in legacy_ids

    def _has_real_completed_run(self, session: Session, user_id: str) -> bool:
        runs = session.scalars(
            select(LessonRun).where(LessonRun.user_id == user_id, LessonRun.completed_at.is_not(None))
        ).all()
        return any(
            not self._is_bootstrap_id(run.id, LEGACY_LESSON_RUN_IDS) and run.recommended_by != "profile_bootstrap"
            for run in runs
        )

    def _has_real_mistakes(self, session: Session, user_id: str) -> bool:
        mistakes = session.scalars(select(MistakeRecord).where(MistakeRecord.user_id == user_id)).all()
        return any(not self._is_bootstrap_id(mistake.id, LEGACY_MISTAKE_IDS) for mistake in mistakes)

    def _has_real_progress_snapshot(self, session: Session, user_id: str) -> bool:
        snapshots = session.scalars(select(ProgressSnapshotModel).where(ProgressSnapshotModel.user_id == user_id)).all()
        return any(not self._is_bootstrap_id(snapshot.id, LEGACY_PROGRESS_IDS) for snapshot in snapshots)

    def _has_real_vocabulary(self, session: Session, user_id: str) -> bool:
        items = session.scalars(select(VocabularyItem).where(VocabularyItem.user_id == user_id)).all()
        return any(not self._is_bootstrap_id(item.id, LEGACY_VOCAB_IDS) for item in items)

    def _has_real_pronunciation_attempts(self, session: Session, user_id: str) -> bool:
        attempts = session.scalars(select(PronunciationAttempt).where(PronunciationAttempt.user_id == user_id)).all()
        return any(not attempt.id.startswith(BASELINE_PREFIX) for attempt in attempts)

    def _ensure_completed_run(
        self,
        session: Session,
        profile: UserProfile,
        template: LessonTemplate,
        spec: dict,
        baseline_key: str,
    ) -> LessonRun:
        run = self._pick_legacy_or_bootstrap_run(session, profile.id, baseline_key)
        now = datetime.utcnow()
        started_at = now - timedelta(hours=2)
        completed_at = started_at + timedelta(minutes=profile.lesson_duration)

        if run is None:
            run = LessonRun(
                id=f"{BASELINE_PREFIX}run-{baseline_key}",
                user_id=profile.id,
                template_id=template.id,
                status=LessonRunStatus.COMPLETED,
                recommended_by="profile_bootstrap",
                weak_spot_ids=[],
                started_at=started_at,
                completed_at=completed_at,
                score=self._run_score(profile),
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
            run.score = self._run_score(profile)

        run.weak_spot_ids = [
            self._mistake_id(baseline_key, "grammar"),
            self._mistake_id(baseline_key, "profession"),
        ]

        existing_block_runs = session.scalars(select(LessonBlockRun).where(LessonBlockRun.lesson_run_id == run.id)).all()
        for block_run in existing_block_runs:
            session.delete(block_run)
        session.flush()

        for index, block in enumerate(sorted(template.blocks, key=lambda item: item.position)):
            response_text, feedback_summary, score = self._block_baseline(block.block_type, spec)
            session.add(
                LessonBlockRun(
                    id=f"{BASELINE_PREFIX}block-run-{baseline_key}-{index}",
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

    @staticmethod
    def _build_block_run_index(lesson_run: LessonRun | None) -> dict[str, str]:
        if lesson_run is None or lesson_run.template is None:
            return {}
        block_type_by_id = {block.id: block.block_type for block in lesson_run.template.blocks}
        return {
            block_type_by_id.get(block_run.block_id, block_run.block_id): block_run.id
            for block_run in lesson_run.block_runs
        }

    @staticmethod
    def _block_baseline(block_type: str, spec: dict) -> tuple[str, str, int]:
        if block_type == "review_block":
            return (
                "I reviewed the corrected versions and repeated the stronger patterns before the next task.",
                "Good reset. The corrected patterns are now easier to activate in context.",
                78,
            )
        if block_type == "grammar_block":
            return (
                spec["grammar"]["corrected_text"],
                "Grammar pattern is clearer. Keep the corrected form active in your next response.",
                74,
            )
        if block_type == "speaking_block":
            return (
                spec["speaking_response"],
                "The answer is clearer and more structured. Keep the same pattern under slight time pressure.",
                76,
            )
        if block_type == "profession_block":
            return (
                spec["profession"]["corrected_text"],
                "Professional tone is stronger now. Keep this phrasing natural and client-friendly.",
                79,
            )
        if block_type == "summary_block":
            return (
                spec["summary_response"],
                "Good wrap-up. One rule and one phrase are now ready to reuse in the next practice round.",
                82,
            )
        return (
            "I completed the block and kept the response concise.",
            "Solid completion. Keep the same level of clarity in the next step.",
            75,
        )

    def _ensure_mistakes(
        self,
        session: Session,
        profile: UserProfile,
        spec: dict,
        baseline_key: str,
        block_run_ids: dict[str, str],
    ) -> None:
        now = datetime.utcnow()
        self._upsert_mistake(
            session,
            profile,
            spec["grammar"],
            self._mistake_id(baseline_key, "grammar"),
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
            self._mistake_id(baseline_key, "profession"),
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
        mistake_spec: dict,
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
        for area, score in self._skill_score_map(profile).items():
            snapshot.skill_scores.append(
                ProgressSkillScore(
                    area=area,
                    score=score,
                    confidence=min(95, score + 16),
                    updated_at=datetime.utcnow(),
                )
            )

    def _ensure_vocabulary(self, session: Session, profile: UserProfile, spec: dict, baseline_key: str) -> None:
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
        spec: dict,
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
                score=max(58, self._level_base(profile.current_level) + 6),
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
        attempt.score = max(58, self._level_base(profile.current_level) + 6)
        attempt.feedback = pronunciation_spec["feedback"]
        attempt.weakest_words = list(pronunciation_spec["weakest_words"])
        attempt.focus_issues = list(pronunciation_spec["focus_issues"])

    @staticmethod
    def _mistake_id(baseline_key: str, slot: str) -> str:
        return f"{BASELINE_PREFIX}mistake-{baseline_key}-{slot}"

    def _pick_legacy_or_bootstrap_run(self, session: Session, user_id: str, baseline_key: str) -> LessonRun | None:
        legacy = session.get(LessonRun, "run-1")
        if legacy is not None and legacy.user_id == user_id:
            return legacy
        return session.get(LessonRun, f"{BASELINE_PREFIX}run-{baseline_key}")

    @classmethod
    def _run_score(cls, profile: UserProfile) -> int:
        weighted_priority = round((profile.speaking_priority + profile.grammar_priority + profile.profession_priority) / 3)
        return max(62, min(88, cls._level_base(profile.current_level) + weighted_priority + 10))

    @staticmethod
    def _level_base(level: str) -> int:
        return LEVEL_BASE_SCORES.get(level.upper(), LEVEL_BASE_SCORES["A2"])

    @classmethod
    def _skill_score_map(cls, profile: UserProfile) -> dict[SkillArea, int]:
        base = cls._level_base(profile.current_level)
        adjustments = TRACK_SCORE_ADJUSTMENTS.get(profile.profession_track, TRACK_SCORE_ADJUSTMENTS["trainer_skills"])
        raw_scores = {
            SkillArea.GRAMMAR: base + adjustments[SkillArea.GRAMMAR] + (profile.grammar_priority - 5) * 2,
            SkillArea.SPEAKING: base + adjustments[SkillArea.SPEAKING] + (profile.speaking_priority - 5) * 2,
            SkillArea.LISTENING: base - 3 + adjustments[SkillArea.LISTENING],
            SkillArea.PRONUNCIATION: base - 5 + adjustments[SkillArea.PRONUNCIATION],
            SkillArea.WRITING: base - 2 + adjustments[SkillArea.WRITING],
            SkillArea.PROFESSION_ENGLISH: base + adjustments[SkillArea.PROFESSION_ENGLISH] + (profile.profession_priority - 5) * 2,
            SkillArea.REGULATION_EU: base - 10 + adjustments[SkillArea.REGULATION_EU],
        }
        return {area: max(18, min(95, value)) for area, value in raw_scores.items()}

    @staticmethod
    def _select_template(session: Session, profession_track: str, preferred_template_id: str) -> LessonTemplate | None:
        template = session.get(LessonTemplate, preferred_template_id)
        if template is not None:
            return template
        templates = session.scalars(select(LessonTemplate).order_by(LessonTemplate.created_at.asc())).all()
        matching = next((item for item in templates if profession_track in (item.enabled_tracks or [])), None)
        return matching or (templates[0] if templates else None)
