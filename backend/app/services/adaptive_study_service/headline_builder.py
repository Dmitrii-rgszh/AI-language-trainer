from __future__ import annotations


def build_headline(name: str, focus_area: str) -> str:
    return f"{name}, today's adaptive focus is {focus_area.replace('_', ' ')}."
