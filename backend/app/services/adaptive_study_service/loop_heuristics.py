from __future__ import annotations

from collections.abc import Sequence

from app.schemas.adaptive import SkillTrajectoryMemory, SkillTrajectorySignal
from app.schemas.mistake import WeakSpot
from app.schemas.progress import ProgressSnapshot
from app.services.shared.recovery_signals import build_mistake_resolution


def build_progress_score_map(progress: ProgressSnapshot | None) -> dict[str, int]:
    if progress is None:
        return {
            "grammar": 0,
            "speaking": 0,
            "listening": 0,
            "pronunciation": 0,
            "writing": 0,
            "profession": 0,
        }

    return {
        "grammar": progress.grammar_score,
        "speaking": progress.speaking_score,
        "listening": progress.listening_score,
        "pronunciation": progress.pronunciation_score,
        "writing": progress.writing_score,
        "profession": progress.profession_score,
    }


def detect_progress_focus(
    progress: ProgressSnapshot | None,
    active_skill_focus: Sequence[str] = (),
) -> str | None:
    if progress is None:
        return None

    score_map = build_progress_score_map(progress)
    measured = {key: value for key, value in score_map.items() if value > 0}
    if not measured:
        return None

    weakest_score = min(measured.values())
    strongest_score = max(measured.values())
    if weakest_score > 55 and strongest_score - weakest_score < 8:
        return None

    weakest_candidates = [
        key for key, value in measured.items() if value == weakest_score
    ]
    normalized_active = [skill.strip() for skill in active_skill_focus if skill and skill.strip()]
    for skill in normalized_active:
        if skill in weakest_candidates:
            return skill
    return weakest_candidates[0] if weakest_candidates else None


def build_progress_trajectory(
    progress_history: Sequence[ProgressSnapshot],
    active_skill_focus: Sequence[str] = (),
) -> SkillTrajectoryMemory | None:
    recent = [item for item in progress_history if item is not None]
    if len(recent) < 2:
        return None

    latest_scores = build_progress_score_map(recent[0])
    oldest_scores = build_progress_score_map(recent[-1])
    normalized_active = [skill.strip() for skill in active_skill_focus if skill and skill.strip()]
    direction_rank = {"slipping": 0, "stable": 1, "improving": 2}
    candidate_signals: list[tuple[tuple[int, int, int, int], SkillTrajectorySignal]] = []

    for skill, current_score in latest_scores.items():
        previous_score = oldest_scores.get(skill, 0)
        if current_score <= 0 or previous_score <= 0:
            continue

        delta = current_score - previous_score
        if delta <= -4:
            direction = "slipping"
            summary = (
                f"{skill} has dropped from {previous_score} to {current_score} across recent sessions, so the route should give it steadier support."
            )
            sort_key = (direction_rank[direction], 0 if skill in normalized_active else 1, current_score, delta)
        elif delta >= 4:
            direction = "improving"
            summary = (
                f"{skill} has climbed from {previous_score} to {current_score}, so the route can build from that stronger signal."
            )
            sort_key = (direction_rank[direction], 0 if skill in normalized_active else 1, -delta, current_score)
        else:
            if current_score > 64:
                continue
            direction = "stable"
            summary = (
                f"{skill} is still hovering around {current_score}/100 across recent sessions, so the route should keep it warm instead of treating it as solved."
            )
            sort_key = (direction_rank[direction], 0 if skill in normalized_active else 1, current_score, abs(delta))

        candidate_signals.append(
            (
                sort_key,
                SkillTrajectorySignal(
                    skill=skill,
                    direction=direction,
                    delta_score=delta,
                    current_score=current_score,
                    summary=summary,
                ),
            )
        )

    if not candidate_signals:
        return None

    candidate_signals.sort(key=lambda item: item[0])
    signals = [signal for _, signal in candidate_signals[:3]]
    focus_signal = signals[0]
    if focus_signal.direction == "slipping":
        memory_summary = (
            f"Across the last {len(recent)} snapshots, {focus_signal.skill} has been slipping, so the route keeps extra support there."
        )
    elif focus_signal.direction == "stable":
        memory_summary = (
            f"Across the last {len(recent)} snapshots, {focus_signal.skill} is still fragile rather than solved, so the route keeps it active."
        )
    else:
        memory_summary = (
            f"Across the last {len(recent)} snapshots, {focus_signal.skill} is improving, so the route can safely build from that momentum."
        )

    return SkillTrajectoryMemory(
        focus_skill=focus_signal.skill,
        direction=focus_signal.direction,
        summary=memory_summary,
        observed_snapshots=len(recent),
        signals=signals,
    )


def detect_listening_focus(
    progress: ProgressSnapshot | None,
    weak_spots: Sequence[WeakSpot],
) -> str | None:
    if any(getattr(spot, "category", "") == "listening" for spot in weak_spots):
        return "audio_comprehension"
    if progress is None:
        return None
    if progress.listening_score <= 55:
        return "audio_comprehension"
    if progress.listening_score < min(progress.speaking_score or 100, progress.writing_score or 100):
        return "detail_capture"
    return None
