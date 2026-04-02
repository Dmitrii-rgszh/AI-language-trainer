from __future__ import annotations

from collections.abc import Sequence


def pick_variant(variants: Sequence[str], *seed_parts: object) -> str:
    if not variants:
        return ""

    seed = "|".join(str(part) for part in seed_parts if part is not None)
    if not seed:
        return variants[0]

    weighted_seed = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    index = (weighted_seed + len(seed_parts) * 17) % len(variants)
    return variants[index]
