from __future__ import annotations

import re
from datetime import datetime, timezone


def normalized_identity(value: str) -> str:
    return value.strip().lower()


def normalize_login_candidate(value: str) -> str:
    compact = re.sub(r"\s+", "_", value.strip().lower())
    compact = re.sub(r"[^\w-]", "", compact, flags=re.UNICODE)
    compact = re.sub(r"_+", "_", compact).strip("_-")
    return compact or "learner"


def compose_login_candidate(base: str, suffix: str) -> str:
    clipped_base = base[: max(1, 64 - len(suffix))]
    return f"{clipped_base}{suffix}"


def build_login_candidates(login: str) -> list[str]:
    base = normalize_login_candidate(login)
    suffixes = [
        "_1",
        "_2",
        "_3",
        "_7",
        f"_{datetime.now(timezone.utc).year}",
        str(datetime.now(timezone.utc).year)[-2:],
        "_pro",
        "_study",
    ]

    candidates: list[str] = []
    seen: set[str] = set()
    for suffix in suffixes:
        candidate = compose_login_candidate(base, suffix)
        lowered = candidate.lower()
        if lowered == base.lower() or lowered in seen:
            continue
        seen.add(lowered)
        candidates.append(candidate)
    return candidates
