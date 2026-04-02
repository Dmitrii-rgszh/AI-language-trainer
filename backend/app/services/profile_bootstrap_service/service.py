from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.schemas.profile import UserProfile

from .baselines import TRACK_BASELINES
from .bootstrap_mistakes import ensure_mistakes
from .bootstrap_progress import ensure_progress_snapshot
from .bootstrap_pronunciation import ensure_pronunciation_attempt
from .bootstrap_run import ensure_completed_run
from .bootstrap_vocabulary import ensure_vocabulary
from .selectors import (
    baseline_key,
    build_block_run_index,
    has_real_completed_run,
    has_real_mistakes,
    has_real_progress_snapshot,
    has_real_pronunciation_attempts,
    has_real_vocabulary,
    select_template,
)


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
                lesson_run = ensure_completed_run(
                    session,
                    profile,
                    template,
                    spec,
                    profile_baseline_key,
                )

            block_run_ids = build_block_run_index(lesson_run)

            if not has_real_mistakes(session, profile.id):
                ensure_mistakes(session, profile, spec, profile_baseline_key, block_run_ids)

            if not has_real_progress_snapshot(session, profile.id):
                ensure_progress_snapshot(session, profile, lesson_run, profile_baseline_key)

            if not has_real_vocabulary(session, profile.id):
                ensure_vocabulary(session, profile, spec, profile_baseline_key)

            if not has_real_pronunciation_attempts(session, profile.id):
                ensure_pronunciation_attempt(session, profile, spec, profile_baseline_key)

            session.commit()
