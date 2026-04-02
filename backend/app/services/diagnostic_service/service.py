from __future__ import annotations

from app.core.errors import ServiceUnavailableError
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas.diagnostic import DiagnosticRoadmap
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile
from app.services.diagnostic_service.roadmap import build_diagnostic_roadmap


class DiagnosticService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        lesson_runtime_repository: LessonRuntimeRepository,
        progress_repository: ProgressRepository,
        mistake_repository: MistakeRepository,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._lesson_runtime_repository = lesson_runtime_repository
        self._progress_repository = progress_repository
        self._mistake_repository = mistake_repository

    def get_roadmap(self, profile: UserProfile) -> DiagnosticRoadmap:
        progress = self._progress_repository.get_latest_snapshot(profile.id)
        weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)
        return build_diagnostic_roadmap(profile, progress, weak_spots)

    def start_checkpoint_run(self, profile: UserProfile) -> LessonRunState:
        template = self._lesson_repository.create_diagnostic_template(
            profession_track=profile.profession_track,
            current_level=profile.current_level,
            target_level=profile.target_level,
        )
        lesson_run = self._lesson_runtime_repository.start_lesson_run(
            user_id=profile.id,
            profession_track=profile.profession_track,
            template_id=template.id,
        )
        if lesson_run is None:
            raise ServiceUnavailableError("Diagnostic checkpoint could not be started.")
        return lesson_run
