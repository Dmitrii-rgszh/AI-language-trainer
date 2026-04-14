from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.models.lesson_run import LessonRun
from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.models.lesson_template import LessonTemplate
from app.repositories.lesson_template_builders import (
    create_diagnostic_template as build_diagnostic_template,
)
from app.repositories.lesson_template_builders import (
    create_recovery_template as build_recovery_template,
)
from app.repositories.lesson_template_selectors import select_template
from app.repositories.lesson_mappers import (
    to_lesson,
    to_lesson_history_item,
    to_lesson_recommendation,
)
from app.schemas.adaptive import VocabularyReviewItem
from app.schemas.blueprint import FeedbackMode
from app.schemas.lesson import Lesson, LessonRecommendation
from app.schemas.mistake import WeakSpot
from app.schemas.progress import LessonHistoryItem


class LessonRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_recommended_lesson(self, profession_track: str | None = None) -> Lesson | None:
        with self._session_factory() as session:
            template = select_template(session, profession_track)
            return to_lesson(template) if template else None

    def get_recommendation(self, profession_track: str | None = None) -> LessonRecommendation | None:
        with self._session_factory() as session:
            template = select_template(session, profession_track)
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
            return build_recovery_template(
                session,
                profession_track,
                weak_spots,
                due_vocabulary,
                listening_focus,
            )

    def create_diagnostic_template(
        self,
        profession_track: str,
        current_level: str,
        target_level: str,
    ) -> LessonTemplate:
        with self._session_factory() as session:
            return build_diagnostic_template(
                session,
                profession_track,
                current_level,
                target_level,
            )

    def create_continuity_template(
        self,
        *,
        profession_track: str,
        continuity_seed: dict,
        weak_spots: list[WeakSpot],
        due_vocabulary: list[VocabularyReviewItem],
    ) -> LessonTemplate | None:
        with self._session_factory() as session:
            base_template = select_template(session, profession_track)
            if not base_template:
                return None

            now = datetime.utcnow()
            template = LessonTemplate(
                id=f"template-continuity-{uuid4().hex[:10]}",
                lesson_type=base_template.lesson_type,
                title=self._build_continuity_title(base_template.title, continuity_seed),
                goal=self._build_continuity_goal(base_template.goal, continuity_seed),
                difficulty=base_template.difficulty,
                estimated_duration=base_template.estimated_duration,
                enabled_tracks=list(base_template.enabled_tracks or []),
                generation_rules=[
                    *(base_template.generation_rules or []),
                    "continuity_seeded",
                    str(continuity_seed.get("focusArea") or "focus"),
                    str(continuity_seed.get("continuityMode") or "guided"),
                ],
                created_at=now,
                updated_at=now,
            )
            session.add(template)
            session.flush()

            blocks: list[LessonBlockModel] = []
            previous_block_id: str | None = None
            for index, source_block in enumerate(base_template.blocks):
                block_id = f"block-continuity-{uuid4().hex[:10]}"
                blocks.append(
                    LessonBlockModel(
                        id=block_id,
                        lesson_template_id=template.id,
                        position=index,
                        block_type=source_block.block_type,
                        title=self._build_continuity_block_title(source_block.title, source_block.block_type, continuity_seed),
                        instructions=self._build_continuity_block_instructions(
                            source_block.instructions,
                            source_block.block_type,
                            continuity_seed,
                            weak_spots=weak_spots,
                        ),
                        estimated_minutes=source_block.estimated_minutes,
                        feedback_mode=source_block.feedback_mode,
                        depends_on_block_ids=[previous_block_id] if previous_block_id else [],
                        payload=self._build_continuity_payload(
                            payload=source_block.payload,
                            block_type=source_block.block_type,
                            continuity_seed=continuity_seed,
                            weak_spots=weak_spots,
                            due_vocabulary=due_vocabulary,
                        ),
                    )
                )
                previous_block_id = block_id

            session.add_all(blocks)
            session.commit()
            session.refresh(template)
            session.refresh(template, attribute_names=["blocks"])
            return template

    def create_guided_route_template(
        self,
        *,
        profession_track: str,
        route_context: dict,
        weak_spots: list[WeakSpot],
        due_vocabulary: list[VocabularyReviewItem],
        continuity_seed: dict | None = None,
    ) -> LessonTemplate | None:
        with self._session_factory() as session:
            base_template = select_template(session, profession_track)
            if not base_template:
                return None

            source_blocks = self._build_guided_route_source_blocks(
                base_template.blocks,
                route_context=route_context,
                due_vocabulary=due_vocabulary,
            )
            now = datetime.utcnow()
            template = LessonTemplate(
                id=f"template-guided-route-{uuid4().hex[:10]}",
                lesson_type=base_template.lesson_type,
                title=self._build_guided_route_title(base_template.title, route_context, continuity_seed),
                goal=self._build_guided_route_goal(base_template.goal, route_context, continuity_seed),
                difficulty=base_template.difficulty,
                estimated_duration=base_template.estimated_duration,
                enabled_tracks=list(base_template.enabled_tracks or []),
                generation_rules=[
                    *(base_template.generation_rules or []),
                    "guided_route_seeded",
                    str(route_context.get("focusArea") or "focus"),
                    str(route_context.get("preferredMode") or "mixed"),
                    str(route_context.get("routeSeedSource") or "daily_loop_plan"),
                    *(
                        [str(continuity_seed.get("continuityMode") or "guided")]
                        if continuity_seed
                        else []
                    ),
                ],
                created_at=now,
                updated_at=now,
            )
            session.add(template)
            session.flush()

            blocks: list[LessonBlockModel] = []
            previous_block_id: str | None = None
            for index, source_block in enumerate(source_blocks):
                block_id = f"block-guided-route-{uuid4().hex[:10]}"
                blocks.append(
                    LessonBlockModel(
                        id=block_id,
                        lesson_template_id=template.id,
                        position=index,
                        block_type=source_block["block_type"],
                        title=self._build_guided_route_block_title(
                            source_block["title"],
                            source_block["block_type"],
                            route_context,
                            continuity_seed,
                        ),
                        instructions=self._build_guided_route_block_instructions(
                            source_block["instructions"],
                            source_block["block_type"],
                            route_context,
                            continuity_seed,
                            weak_spots=weak_spots,
                        ),
                        estimated_minutes=source_block["estimated_minutes"],
                        feedback_mode=source_block["feedback_mode"],
                        depends_on_block_ids=[previous_block_id] if previous_block_id else [],
                        payload=self._build_guided_route_payload(
                            payload=source_block["payload"],
                            block_type=source_block["block_type"],
                            route_context=route_context,
                            continuity_seed=continuity_seed,
                            weak_spots=weak_spots,
                            due_vocabulary=due_vocabulary,
                        ),
                    )
                )
                previous_block_id = block_id

            session.add_all(blocks)
            session.commit()
            session.refresh(template)
            session.refresh(template, attribute_names=["blocks"])
            return template

    @staticmethod
    def _serialize_source_block(block: LessonBlockModel) -> dict:
        return {
            "block_type": block.block_type,
            "title": block.title,
            "instructions": block.instructions,
            "estimated_minutes": block.estimated_minutes,
            "feedback_mode": block.feedback_mode,
            "payload": dict(block.payload or {}),
        }

    @classmethod
    def _build_guided_route_source_blocks(
        cls,
        base_blocks: list[LessonBlockModel],
        *,
        route_context: dict,
        due_vocabulary: list[VocabularyReviewItem],
    ) -> list[dict]:
        specs = [cls._serialize_source_block(block) for block in base_blocks]
        module_rotation_keys = {
            str(item)
            for item in route_context.get("moduleRotationKeys", [])
            if isinstance(item, str) and item
        }
        practice_mix = cls._build_practice_mix_map(route_context)
        lead_module = cls._resolve_guided_route_lead_module(route_context, practice_mix)
        elevated_modules = {
            module_key
            for module_key, item in practice_mix.items()
            if isinstance(item, dict)
            and (
                item.get("emphasis") in {"lead", "support"}
                or (isinstance(item.get("share"), int) and item["share"] >= 14)
            )
        }
        target_support_modules = module_rotation_keys | elevated_modules

        if "vocabulary" in target_support_modules and due_vocabulary and not any(
            spec["block_type"] == "vocab_block" for spec in specs
        ):
            insert_at = next(
                (index + 1 for index, spec in enumerate(specs) if spec["block_type"] == "review_block"),
                0,
            )
            specs.insert(insert_at, cls._build_guided_vocab_support_block(route_context, due_vocabulary))

        if "grammar" in target_support_modules and not any(
            spec["block_type"] == "grammar_block" for spec in specs
        ):
            insert_at = next(
                (
                    index + 1
                    for index, spec in enumerate(specs)
                    if spec["block_type"] in {"review_block", "vocab_block"}
                ),
                0,
            )
            specs.insert(insert_at, cls._build_guided_grammar_support_block(route_context))

        if "listening" in target_support_modules and not any(
            spec["block_type"] == "listening_block" for spec in specs
        ):
            insert_before = next(
                (
                    index
                    for index, spec in enumerate(specs)
                    if spec["block_type"] in {"speaking_block", "writing_block", "profession_block", "summary_block"}
                ),
                len(specs),
            )
            specs.insert(insert_before, cls._build_guided_listening_support_block(route_context))

        if "profession" in target_support_modules and not any(
            spec["block_type"] == "profession_block" for spec in specs
        ):
            insert_before = next(
                (
                    index
                    for index, spec in enumerate(specs)
                    if spec["block_type"] == "summary_block"
                ),
                len(specs),
            )
            specs.insert(insert_before, cls._build_guided_profession_support_block(route_context))

        if "pronunciation" in target_support_modules and not any(
            spec["block_type"] == "pronunciation_block" for spec in specs
        ):
            insert_before = next(
                (
                    index
                    for index, spec in enumerate(specs)
                    if spec["block_type"] == "summary_block"
                ),
                len(specs),
            )
            specs.insert(insert_before, cls._build_guided_pronunciation_support_block(route_context))

        if route_context.get("preferredMode") == "text_first":
            specs = cls._prefer_text_first_response(specs, route_context)

        specs = cls._rebalance_guided_route_sequence(specs, lead_module=lead_module)
        return cls._rebalance_guided_route_block_minutes(specs, practice_mix=practice_mix)

    @staticmethod
    def _build_guided_vocab_support_block(
        route_context: dict,
        due_vocabulary: list[VocabularyReviewItem],
    ) -> dict:
        focus_area = route_context.get("focusArea") or "today's route"
        return {
            "block_type": "vocab_block",
            "title": "Route vocabulary warm-up",
            "instructions": f"Bring back the active words that can make {focus_area} feel easier in the response blocks.",
            "estimated_minutes": 4,
            "feedback_mode": FeedbackMode.AFTER_BLOCK,
            "payload": {
                "lexical_set": "guided_route_support",
                "vocabulary_ids": [item.id for item in due_vocabulary[:4]],
                "phrases": [item.context for item in due_vocabulary[:4]],
            },
        }

    @staticmethod
    def _build_guided_listening_support_block(route_context: dict) -> dict:
        focus_area = route_context.get("focusArea") or "today's route"
        primary_goal = route_context.get("primaryGoal") or "your main goal"
        carry_over = route_context.get("carryOverSignalLabel") or focus_area
        watch_signal = route_context.get("watchSignalLabel") or focus_area
        transcript = (
            f"I have kept today's route centered on {focus_area}, reused {carry_over}, "
            f"and checked whether {watch_signal} still needs more support before the next response."
        )
        return {
            "block_type": "listening_block",
            "title": "Listening route support",
            "instructions": f"Listen for cues about {focus_area} and notice how they connect back to {primary_goal}.",
            "estimated_minutes": 4,
            "feedback_mode": FeedbackMode.AFTER_BLOCK,
            "payload": {
                "audio_variants": [
                    {
                        "id": "guided-route-listening-support",
                        "label": "Route support update",
                        "transcript": transcript,
                        "questions": [
                            {
                                "prompt": "What is the route centered on?",
                                "acceptable_answers": [str(focus_area), f"centered on {focus_area}"],
                            },
                            {
                                "prompt": "What still needs watching?",
                                "acceptable_answers": [str(watch_signal), f"{watch_signal} still needs more support"],
                            },
                        ],
                    }
                ],
                "questions": [
                    "What is the route centered on?",
                    "What still needs watching?",
                ],
                "answer_key": [str(focus_area), str(watch_signal)],
                "slow_mode_allowed": True,
            },
        }

    @staticmethod
    def _build_guided_grammar_support_block(route_context: dict) -> dict:
        focus_area = route_context.get("focusArea") or "today's route"
        primary_goal = route_context.get("primaryGoal") or "your main goal"
        watch_signal = route_context.get("watchSignalLabel") or focus_area
        weak_spot_categories = [
            str(item)
            for item in route_context.get("weakSpotCategories", [])
            if isinstance(item, str) and item
        ][:3]
        return {
            "block_type": "grammar_block",
            "title": "Grammar route anchor",
            "instructions": f"Lock in the grammar move that today's {focus_area} route depends on before you widen the response.",
            "estimated_minutes": 4,
            "feedback_mode": FeedbackMode.AFTER_BLOCK,
            "payload": {
                "topic_id": "guided-route-grammar-support",
                "focus_points": [str(focus_area), str(watch_signal)],
                "prompts": [
                    f"Write one sentence that keeps {focus_area} clear and useful for {primary_goal}.",
                    f"Rewrite one sentence so {watch_signal} does not slip back in.",
                ],
                "target_error_types": weak_spot_categories,
            },
        }

    @staticmethod
    def _build_guided_profession_support_block(route_context: dict) -> dict:
        focus_area = route_context.get("focusArea") or "today's route"
        profession_track = route_context.get("professionTrack") or "general"
        primary_goal = route_context.get("primaryGoal") or "your main goal"
        return {
            "block_type": "profession_block",
            "title": "Professional route framing",
            "instructions": f"Keep {focus_area} grounded in a real-world scenario so the route stays useful, not generic.",
            "estimated_minutes": 4,
            "feedback_mode": FeedbackMode.IMMEDIATE,
            "payload": {
                "domain": profession_track,
                "topicId": "guided-route-profession-support",
                "scenario": f"Short work scenario aligned with {primary_goal}",
                "targetTerms": [str(focus_area), "next step", "clear update"],
            },
        }

    @staticmethod
    def _build_guided_pronunciation_support_block(route_context: dict) -> dict:
        focus_area = route_context.get("focusArea") or "today's route"
        carry_over = route_context.get("carryOverSignalLabel") or focus_area
        return {
            "block_type": "pronunciation_block",
            "title": "Pronunciation route control",
            "instructions": f"Say the route phrases out loud and keep {carry_over} stable while the session is still fresh.",
            "estimated_minutes": 3,
            "feedback_mode": FeedbackMode.AFTER_BLOCK,
            "payload": {
                "sound_focus": ["sentence stress", "clarity"],
                "phrase_drills": [
                    f"I have kept today's route focused on {focus_area}.",
                    f"Could you help me with the next step for {carry_over}?",
                ],
                "minimal_pairs": ["focus/focused", "step/steps"],
                "shadowing_script": f"I have kept today's route focused on {focus_area}.",
            },
        }

    @staticmethod
    def _prefer_text_first_response(
        specs: list[dict],
        route_context: dict,
    ) -> list[dict]:
        transformed: list[dict] = []
        speaking_converted = False
        focus_area = route_context.get("focusArea") or "today's route"

        for spec in specs:
            if spec["block_type"] == "speaking_block" and not speaking_converted:
                payload = dict(spec["payload"] or {})
                prompts = payload.get("prompts") if isinstance(payload.get("prompts"), list) else []
                feedback_focus = (
                    payload.get("feedbackFocus")
                    if isinstance(payload.get("feedbackFocus"), list)
                    else payload.get("feedback_focus")
                    if isinstance(payload.get("feedback_focus"), list)
                    else []
                )
                transformed.append(
                    {
                        **spec,
                        "block_type": "writing_block",
                        "title": "Guided writing response",
                        "instructions": f"Сначала собери короткий письменный ответ, чтобы спокойно выстроить {focus_area}, а потом при желании проговори его.",
                        "payload": {
                            "task_id": "guided-route-writing-response",
                            "brief": "Answer the guided prompts as one short, clear written response.",
                            "prompts": prompts,
                            "checklist": feedback_focus or ["clarity", "structure", "accuracy"],
                            "tone": "clear and natural",
                            "sourceScenarioId": payload.get("scenarioId") or payload.get("scenario_id"),
                        },
                    }
                )
                speaking_converted = True
                continue

            transformed.append(spec)

        return transformed

    @staticmethod
    def _build_continuity_title(base_title: str, continuity_seed: dict) -> str:
        focus_area = continuity_seed.get("focusArea") or "next focus"
        carry_over = continuity_seed.get("carryOverSignalLabel")
        if carry_over:
            return f"{base_title}: carry {carry_over} into {focus_area}"
        return f"{base_title}: next-day continuity around {focus_area}"

    @classmethod
    def _build_guided_route_title(
        cls,
        base_title: str,
        route_context: dict,
        continuity_seed: dict | None,
    ) -> str:
        if continuity_seed:
            return cls._build_continuity_title(base_title, continuity_seed)

        focus_area = route_context.get("focusArea") or "today's focus"
        return f"{base_title}: guided route for {focus_area}"

    @staticmethod
    def _build_continuity_goal(base_goal: str, continuity_seed: dict) -> str:
        carry_over = continuity_seed.get("carryOverSignalLabel") or continuity_seed.get("focusArea") or "today's signal"
        watch_signal = continuity_seed.get("watchSignalLabel") or continuity_seed.get("focusArea") or "the weak signal"
        return (
            f"{base_goal} This run carries forward {carry_over} and keeps a close watch on {watch_signal} so the route stays continuous."
        )

    @classmethod
    def _build_guided_route_goal(
        cls,
        base_goal: str,
        route_context: dict,
        continuity_seed: dict | None,
    ) -> str:
        goal = cls._build_continuity_goal(base_goal, continuity_seed) if continuity_seed else base_goal
        primary_goal = route_context.get("primaryGoal")
        why_now = route_context.get("whyNow")
        if primary_goal and why_now:
            return f"{goal} This route is tuned to {primary_goal}. {why_now}"
        if why_now:
            return f"{goal} {why_now}"
        return goal

    @staticmethod
    def _build_continuity_block_title(base_title: str, block_type: str, continuity_seed: dict) -> str:
        carry_over = continuity_seed.get("carryOverSignalLabel")
        watch_signal = continuity_seed.get("watchSignalLabel")
        if block_type == "summary_block" and watch_signal:
            return f"{base_title}: lock in {watch_signal}"
        if block_type in {"review_block", "grammar_block", "speaking_block"} and carry_over:
            return f"{base_title}: carry {carry_over}"
        return base_title

    @classmethod
    def _build_guided_route_block_title(
        cls,
        base_title: str,
        block_type: str,
        route_context: dict,
        continuity_seed: dict | None,
    ) -> str:
        title = (
            cls._build_continuity_block_title(base_title, block_type, continuity_seed)
            if continuity_seed
            else base_title
        )
        focus_area = route_context.get("focusArea")
        if (
            focus_area
            and block_type in {"grammar_block", "speaking_block", "writing_block", "profession_block"}
            and str(focus_area).lower() not in title.lower()
        ):
            return f"{title}: {focus_area} focus"
        if block_type == "summary_block" and focus_area:
            return f"{title}: next move for {focus_area}"
        return title

    @staticmethod
    def _build_continuity_block_instructions(
        base_instructions: str,
        block_type: str,
        continuity_seed: dict,
        *,
        weak_spots: list[WeakSpot],
    ) -> str:
        carry_over = continuity_seed.get("carryOverSignalLabel") or continuity_seed.get("focusArea") or "today's signal"
        watch_signal = continuity_seed.get("watchSignalLabel") or continuity_seed.get("focusArea") or "the weak signal"
        top_weak_spot = weak_spots[0].title if weak_spots else watch_signal
        if block_type == "review_block":
            return f"{base_instructions} Start by recalling {carry_over} and keep {top_weak_spot} visible from the first answer."
        if block_type == "grammar_block":
            return f"{base_instructions} Use this block to protect {top_weak_spot} while you carry forward {carry_over}."
        if block_type == "speaking_block":
            return f"{base_instructions} Keep {carry_over} alive in your response and do not let {top_weak_spot} slip back in."
        if block_type == "summary_block":
            return f"{base_instructions} Name what carried forward, what still needs watching, and how tomorrow's route should respond."
        return base_instructions

    @classmethod
    def _build_guided_route_block_instructions(
        cls,
        base_instructions: str,
        block_type: str,
        route_context: dict,
        continuity_seed: dict | None,
        *,
        weak_spots: list[WeakSpot],
    ) -> str:
        instructions = (
            cls._build_continuity_block_instructions(
                base_instructions,
                block_type,
                continuity_seed,
                weak_spots=weak_spots,
            )
            if continuity_seed
            else base_instructions
        )
        focus_area = route_context.get("focusArea") or "today's focus"
        primary_goal = route_context.get("primaryGoal") or "the main goal"
        preferred_mode = route_context.get("preferredMode") or "mixed"
        next_best_action = route_context.get("nextBestAction") or "keep the route moving"
        top_weak_spot = weak_spots[0].title if weak_spots else focus_area

        if block_type == "review_block":
            return f"{instructions} Use this review to anchor {focus_area} before the larger response block."
        if block_type == "grammar_block":
            return f"{instructions} Keep the grammar move useful for {primary_goal} and protect {top_weak_spot}."
        if block_type == "listening_block":
            return f"{instructions} Listen for cues that support {focus_area} and notice where {top_weak_spot} can still drift."
        if block_type == "speaking_block":
            mode_line = (
                "Answer spoken-first and keep it natural."
                if preferred_mode == "voice_first"
                else "You can sketch a short draft first, then turn it into a spoken answer."
            )
            return f"{instructions} {mode_line} Keep it useful for {primary_goal}."
        if block_type == "writing_block":
            mode_line = (
                "Draft it clearly before expanding."
                if preferred_mode == "text_first"
                else "Write from the spoken idea you would naturally use."
            )
            return f"{instructions} {mode_line} Keep it aligned with {primary_goal}."
        if block_type == "profession_block":
            return f"{instructions} Keep the language aligned with {primary_goal} instead of sounding generic."
        if block_type == "summary_block":
            return f"{instructions} End by naming what moved {focus_area} and how the next route should respond. {next_best_action}"
        return instructions

    @staticmethod
    def _build_continuity_payload(
        *,
        payload: dict,
        block_type: str,
        continuity_seed: dict,
        weak_spots: list[WeakSpot],
        due_vocabulary: list[VocabularyReviewItem],
    ) -> dict:
        enriched_payload = dict(payload or {})
        weak_spot_titles = [spot.title for spot in weak_spots[:3]]
        weak_spot_categories = [spot.category for spot in weak_spots[:3]]
        due_words = [item.word for item in due_vocabulary[:4]]
        due_contexts = [item.context for item in due_vocabulary[:2]]
        continuity_payload = {
            "focusArea": continuity_seed.get("focusArea"),
            "continuityMode": continuity_seed.get("continuityMode"),
            "carryOverSignalLabel": continuity_seed.get("carryOverSignalLabel"),
            "watchSignalLabel": continuity_seed.get("watchSignalLabel"),
            "strategyShift": continuity_seed.get("strategyShift"),
            "sessionHeadline": continuity_seed.get("headline"),
            "weakSpotTitles": weak_spot_titles,
            "dueVocabularyWords": due_words,
        }
        enriched_payload["continuity"] = continuity_payload

        carry_over = continuity_seed.get("carryOverSignalLabel")
        watch_signal = continuity_seed.get("watchSignalLabel")

        if block_type == "review_block":
            review_items = enriched_payload.get("reviewItems") or enriched_payload.get("review_items")
            if isinstance(review_items, list):
                review_items = [*review_items, *weak_spot_titles[:2], *due_words[:2]]
                if "reviewItems" in enriched_payload:
                    enriched_payload["reviewItems"] = review_items
                else:
                    enriched_payload["review_items"] = review_items

        if block_type == "vocab_block":
            phrases = enriched_payload.get("phrases")
            if isinstance(phrases, list) and due_contexts:
                enriched_payload["phrases"] = [*phrases, *due_contexts]
            if due_words:
                existing_ids = enriched_payload.get("vocabulary_ids")
                if isinstance(existing_ids, list):
                    enriched_payload["continuityVocabularyWords"] = due_words

        if block_type in {"speaking_block", "grammar_block"}:
            prompts = enriched_payload.get("prompts")
            if isinstance(prompts, list):
                if carry_over:
                    prompts = [*prompts, f"Carry forward this signal in your answer: {carry_over}."]
                if watch_signal:
                    prompts = [*prompts, f"Avoid slipping back into this weak signal: {watch_signal}."]
                if weak_spot_titles:
                    prompts = [*prompts, f"Keep this repeated weak spot under control: {weak_spot_titles[0]}."]
                if due_words:
                    prompts = [*prompts, f"If possible, reuse one active word from the queue: {due_words[0]}."]
                enriched_payload["prompts"] = prompts
            feedback_focus = enriched_payload.get("feedbackFocus") or enriched_payload.get("feedback_focus")
            if isinstance(feedback_focus, list):
                merged_feedback_focus = [*feedback_focus, *[spot for spot in weak_spot_titles[:2] if spot not in feedback_focus]]
                if "feedbackFocus" in enriched_payload:
                    enriched_payload["feedbackFocus"] = merged_feedback_focus
                else:
                    enriched_payload["feedback_focus"] = merged_feedback_focus
            target_error_types = enriched_payload.get("targetErrorTypes") or enriched_payload.get("target_error_types")
            if isinstance(target_error_types, list):
                merged_error_types = [*target_error_types, *[category for category in weak_spot_categories if category not in target_error_types]]
                if "targetErrorTypes" in enriched_payload:
                    enriched_payload["targetErrorTypes"] = merged_error_types
                else:
                    enriched_payload["target_error_types"] = merged_error_types

        if block_type == "profession_block":
            target_terms = enriched_payload.get("targetTerms") or enriched_payload.get("target_terms")
            if isinstance(target_terms, list) and due_words:
                merged_terms = [*target_terms, *[word for word in due_words[:2] if word not in target_terms]]
                if "targetTerms" in enriched_payload:
                    enriched_payload["targetTerms"] = merged_terms
                else:
                    enriched_payload["target_terms"] = merged_terms

        if block_type == "summary_block":
            recap_prompts = enriched_payload.get("recapPrompts") or enriched_payload.get("recap_prompts")
            if isinstance(recap_prompts, list):
                recap_prompts = [
                    *recap_prompts,
                    f"What signal do you want to carry forward from this run: {carry_over or continuity_seed.get('focusArea') or 'current focus'}?",
                    f"What still needs watching next: {watch_signal or continuity_seed.get('focusArea') or 'weak signal'}?",
                    *(
                        [f"Which repeated weak spot looked better today: {weak_spot_titles[0]}?"]
                        if weak_spot_titles
                        else []
                    ),
                ]
                if "recapPrompts" in enriched_payload:
                    enriched_payload["recapPrompts"] = recap_prompts
                else:
                    enriched_payload["recap_prompts"] = recap_prompts
            if continuity_seed.get("strategyShift"):
                if "nextStep" in enriched_payload:
                    enriched_payload["nextStep"] = continuity_seed["strategyShift"]
                elif "next_step" in enriched_payload:
                    enriched_payload["next_step"] = continuity_seed["strategyShift"]

        return enriched_payload

    @classmethod
    def _build_guided_route_payload(
        cls,
        *,
        payload: dict,
        block_type: str,
        route_context: dict,
        continuity_seed: dict | None,
        weak_spots: list[WeakSpot],
        due_vocabulary: list[VocabularyReviewItem],
    ) -> dict:
        enriched_payload = dict(payload or {})
        weak_spot_titles = [spot.title for spot in weak_spots[:3]]
        weak_spot_categories = [spot.category for spot in weak_spots[:3]]
        due_words = [item.word for item in due_vocabulary[:4]]
        active_skill_focus = [
            str(item)
            for item in route_context.get("activeSkillFocus", [])
            if isinstance(item, str) and item
        ][:3]
        module_rotation_keys = [
            str(item)
            for item in route_context.get("moduleRotationKeys", [])
            if isinstance(item, str) and item
        ][:3]
        module_rotation_titles = [
            str(item)
            for item in route_context.get("moduleRotationTitles", [])
            if isinstance(item, str) and item
        ][:3]
        practice_mix = [
            item
            for item in route_context.get("practiceMix", [])
            if isinstance(item, dict) and item.get("moduleKey")
        ][:5]
        weak_spot_categories = [
            str(item)
            for item in route_context.get("weakSpotCategories", [])
            if isinstance(item, str) and item
        ][:3]
        preferred_mode = route_context.get("preferredMode")
        primary_goal = route_context.get("primaryGoal")
        focus_area = route_context.get("focusArea")
        practice_shift_summary = (
            str(route_context.get("practiceShiftSummary"))
            if route_context.get("practiceShiftSummary")
            else None
        )
        lead_practice_title = (
            str(route_context.get("leadPracticeTitle"))
            if route_context.get("leadPracticeTitle")
            else None
        )
        weakest_practice_title = (
            str(route_context.get("weakestPracticeTitle"))
            if route_context.get("weakestPracticeTitle")
            else None
        )
        skill_trajectory_summary = (
            str(route_context.get("skillTrajectorySummary"))
            if route_context.get("skillTrajectorySummary")
            else None
        )
        skill_trajectory_focus = (
            str(route_context.get("skillTrajectoryFocus"))
            if route_context.get("skillTrajectoryFocus")
            else None
        )
        skill_trajectory_direction = (
            str(route_context.get("skillTrajectoryDirection"))
            if route_context.get("skillTrajectoryDirection")
            else None
        )

        enriched_payload["routeContext"] = {
            "focusArea": focus_area,
            "sessionKind": route_context.get("sessionKind"),
            "routeHeadline": route_context.get("routeHeadline"),
            "whyNow": route_context.get("whyNow"),
            "nextBestAction": route_context.get("nextBestAction"),
            "primaryGoal": primary_goal,
            "preferredMode": preferred_mode,
            "routeSeedSource": route_context.get("routeSeedSource"),
            "inputLane": route_context.get("inputLane"),
            "outputLane": route_context.get("outputLane"),
            "moduleRotationKeys": module_rotation_keys,
            "moduleRotationTitles": module_rotation_titles,
            "practiceMix": practice_mix,
            "skillTrajectory": route_context.get("skillTrajectory"),
            "skillTrajectorySummary": skill_trajectory_summary,
            "skillTrajectoryFocus": skill_trajectory_focus,
            "skillTrajectoryDirection": skill_trajectory_direction,
            "practiceShiftSummary": practice_shift_summary,
            "leadPracticeTitle": lead_practice_title,
            "weakestPracticeTitle": weakest_practice_title,
            "activeSkillFocus": active_skill_focus,
            "weakSpotTitles": weak_spot_titles,
            "weakSpotCategories": weak_spot_categories,
            "dueVocabularyWords": due_words,
            "carryOverSignalLabel": (
                continuity_seed.get("carryOverSignalLabel") if continuity_seed else None
            ),
            "watchSignalLabel": (
                continuity_seed.get("watchSignalLabel")
                if continuity_seed
                else weak_spot_titles[0] if weak_spot_titles else None
            ),
        }

        if continuity_seed:
            enriched_payload = cls._build_continuity_payload(
                payload=enriched_payload,
                block_type=block_type,
                continuity_seed=continuity_seed,
                weak_spots=weak_spots,
                due_vocabulary=due_vocabulary,
            )

        if block_type == "review_block":
            cls._merge_payload_list(
                enriched_payload,
                keys=("reviewItems", "review_items"),
                additions=[*weak_spot_titles[:2], *due_words[:2]],
            )
            cls._merge_payload_list(
                enriched_payload,
                keys=("reviewItems", "review_items"),
                additions=[practice_shift_summary] if practice_shift_summary else [],
            )

        if block_type == "grammar_block":
            cls._merge_payload_list(
                enriched_payload,
                keys=("focusPoints", "focus_points"),
                additions=[item for item in [str(focus_area) if focus_area else None, *active_skill_focus] if item],
            )
            cls._merge_payload_list(
                enriched_payload,
                keys=("prompts",),
                additions=[
                    f"Keep the grammar move useful for {primary_goal}." if primary_goal else "",
                    f"Protect this weak signal while answering: {weak_spot_titles[0]}." if weak_spot_titles else "",
                    f"Reuse this active word if you can: {due_words[0]}." if due_words else "",
                    (
                        f"Yesterday {weakest_practice_title} stayed weaker, so use this block to support it before the route widens."
                        if weakest_practice_title
                        else ""
                    ),
                    (
                        f"Multi-day memory says {skill_trajectory_focus} has been {skill_trajectory_direction}, so keep this block steadier there."
                        if skill_trajectory_focus and skill_trajectory_direction in {"slipping", "stable"}
                        else ""
                    ),
                ],
            )
            cls._merge_payload_list(
                enriched_payload,
                keys=("targetErrorTypes", "target_error_types"),
                additions=weak_spot_categories,
            )

        if block_type in {"speaking_block", "writing_block"}:
            cls._merge_payload_list(
                enriched_payload,
                keys=("prompts",),
                additions=[
                    f"Make the response useful for {primary_goal}." if primary_goal else "",
                    (
                        "Keep the answer spoken-first and concise."
                        if preferred_mode == "voice_first"
                        else "You can draft the answer briefly before expanding."
                    ),
                    f"Keep the route focused on {focus_area}." if focus_area else "",
                    f"Try to reuse this active word: {due_words[0]}." if due_words else "",
                    (
                        f"Yesterday {lead_practice_title} carried the route best, so let this response inherit that stability."
                        if lead_practice_title
                        else ""
                    ),
                    (
                        skill_trajectory_summary
                        if skill_trajectory_summary and skill_trajectory_direction in {"slipping", "stable"}
                        else ""
                    ),
                ],
            )
            cls._merge_payload_list(
                enriched_payload,
                keys=("feedbackFocus", "feedback_focus"),
                additions=[
                    *weak_spot_titles[:2],
                    *(active_skill_focus[:1] if active_skill_focus else []),
                ],
            )

        if block_type == "listening_block":
            enriched_payload["routeFocusHint"] = (
                f"Listen for cues that support {focus_area} and notice whether {weak_spot_titles[0]} still feels shaky."
                if weak_spot_titles and focus_area
                else f"Listen for cues that support {focus_area}."
                if focus_area
                else enriched_payload.get("routeFocusHint")
            )
            if practice_shift_summary:
                enriched_payload["routePracticeShift"] = practice_shift_summary
            if skill_trajectory_summary:
                enriched_payload["routeTrajectory"] = skill_trajectory_summary

        if block_type == "profession_block":
            cls._merge_payload_list(
                enriched_payload,
                keys=("targetTerms", "target_terms"),
                additions=due_words[:2],
            )
            if primary_goal:
                enriched_payload["routeScenarioFocus"] = (
                    f"Keep this block directly useful for {primary_goal}."
                )

        if block_type == "summary_block":
            cls._merge_payload_list(
                enriched_payload,
                keys=("recapPrompts", "recap_prompts"),
                additions=[
                    f"What part of today's route felt most useful for {primary_goal}?" if primary_goal else "",
                    f"What should stay active around {focus_area} tomorrow?" if focus_area else "",
                    (
                        f"Did the route do a better job supporting {weakest_practice_title} this time?"
                        if weakest_practice_title
                        else ""
                    ),
                    skill_trajectory_summary or "",
                ],
            )
            next_best_action = route_context.get("nextBestAction")
            if next_best_action:
                if "nextStep" in enriched_payload:
                    enriched_payload["nextStep"] = next_best_action
                else:
                    enriched_payload["next_step"] = next_best_action

        return enriched_payload

    @staticmethod
    def _build_practice_mix_map(route_context: dict) -> dict[str, dict]:
        practice_mix_map: dict[str, dict] = {}
        for item in route_context.get("practiceMix", []):
            if not isinstance(item, dict):
                continue
            module_key = item.get("moduleKey")
            if not isinstance(module_key, str) or not module_key:
                continue
            practice_mix_map[module_key] = item
        return practice_mix_map

    @classmethod
    def _resolve_guided_route_lead_module(
        cls,
        route_context: dict,
        practice_mix: dict[str, dict],
    ) -> str | None:
        lead_item = next(
            (
                item
                for item in route_context.get("practiceMix", [])
                if isinstance(item, dict) and item.get("emphasis") == "lead" and item.get("moduleKey")
            ),
            None,
        )
        if isinstance(lead_item, dict) and isinstance(lead_item.get("moduleKey"), str):
            return lead_item["moduleKey"]
        module_rotation = route_context.get("moduleRotationKeys", [])
        if isinstance(module_rotation, list) and module_rotation:
            first_key = module_rotation[0]
            if isinstance(first_key, str) and first_key:
                return first_key
        if practice_mix:
            return next(iter(practice_mix))
        return None

    @classmethod
    def _rebalance_guided_route_sequence(
        cls,
        specs: list[dict],
        *,
        lead_module: str | None,
    ) -> list[dict]:
        if not lead_module:
            return specs

        if lead_module == "grammar":
            return cls._move_block_before_types(specs, "grammar_block", {"listening_block", "speaking_block", "writing_block", "profession_block"})
        if lead_module == "listening":
            return cls._move_block_before_types(specs, "listening_block", {"speaking_block", "writing_block", "profession_block"})
        if lead_module == "profession":
            return cls._move_block_before_types(specs, "profession_block", {"speaking_block", "writing_block", "summary_block"})
        if lead_module == "pronunciation":
            return cls._move_block_before_types(specs, "pronunciation_block", {"speaking_block", "writing_block", "summary_block"})
        if lead_module == "vocabulary":
            return cls._move_block_before_types(specs, "vocab_block", {"grammar_block", "listening_block", "speaking_block", "writing_block"})
        return specs

    @staticmethod
    def _move_block_before_types(
        specs: list[dict],
        block_type: str,
        target_types: set[str],
    ) -> list[dict]:
        source_index = next((index for index, spec in enumerate(specs) if spec["block_type"] == block_type), None)
        if source_index is None:
            return specs
        target_index = next((index for index, spec in enumerate(specs) if spec["block_type"] in target_types), None)
        if target_index is None or source_index < target_index:
            return specs

        reordered = list(specs)
        block = reordered.pop(source_index)
        reordered.insert(target_index, block)
        return reordered

    @classmethod
    def _rebalance_guided_route_block_minutes(
        cls,
        specs: list[dict],
        *,
        practice_mix: dict[str, dict],
    ) -> list[dict]:
        rebalanced: list[dict] = []
        lead_module = next(
            (
                module_key
                for module_key, item in practice_mix.items()
                if isinstance(item, dict) and item.get("emphasis") == "lead"
            ),
            None,
        )

        for spec in specs:
            module_key = cls._map_block_type_to_module_key(spec["block_type"])
            item = practice_mix.get(module_key, {})
            share = item.get("share") if isinstance(item, dict) else None
            emphasis = item.get("emphasis") if isinstance(item, dict) else None
            minutes = int(spec["estimated_minutes"])

            if emphasis == "lead" and module_key not in {"lesson"}:
                minutes += 2 if minutes <= 4 else 1
            elif emphasis == "support":
                minutes += 1 if minutes <= 3 else 0
            elif share is not None and isinstance(share, int) and share <= 8 and module_key not in {"lesson"}:
                minutes = max(2, minutes - 1)

            if spec["block_type"] == "summary_block" and lead_module and lead_module != "lesson":
                minutes = max(minutes, 4)

            rebalanced.append(
                {
                    **spec,
                    "estimated_minutes": minutes,
                }
            )
        return rebalanced

    @staticmethod
    def _map_block_type_to_module_key(block_type: str) -> str:
        return {
            "review_block": "lesson",
            "summary_block": "lesson",
            "vocab_block": "vocabulary",
            "grammar_block": "grammar",
            "listening_block": "listening",
            "speaking_block": "speaking",
            "writing_block": "writing",
            "profession_block": "profession",
            "pronunciation_block": "pronunciation",
        }.get(block_type, "lesson")

    @staticmethod
    def _merge_payload_list(
        payload: dict,
        *,
        keys: tuple[str, ...],
        additions: list[str],
    ) -> None:
        normalized = [item for item in additions if item]
        if not normalized:
            return

        target_key = next((key for key in keys if isinstance(payload.get(key), list)), keys[0])
        existing = payload.get(target_key)
        merged = [*existing] if isinstance(existing, list) else []
        for item in normalized:
            if item not in merged:
                merged.append(item)
        payload[target_key] = merged
