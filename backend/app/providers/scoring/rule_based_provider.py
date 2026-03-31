from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.providers.scoring.base import BaseScoringProvider
from app.schemas.provider import ProviderAvailability, ProviderStatus


class RuleBasedScoringProvider(BaseScoringProvider):
    def score(self, content: str) -> int:
        word_count = len(self._normalize(content))
        if word_count <= 2:
            return 45
        if word_count <= 5:
            return 62
        if word_count <= 10:
            return 74
        return 82

    def score_pronunciation(self, target_text: str, transcript: str) -> dict[str, object]:
        target_tokens = self._normalize(target_text)
        transcript_tokens = self._normalize(transcript)
        if not target_tokens:
            return {
                "score": 0,
                "matched_tokens": [],
                "missed_tokens": [],
                "feedback": "Target phrase is empty, so pronunciation scoring could not run.",
                "weakest_words": [],
                "word_assessments": [],
                "focus_assessments": [],
            }

        matched = [token for token in target_tokens if token in transcript_tokens]
        missed = [token for token in target_tokens if token not in transcript_tokens]
        token_ratio = len(matched) / len(target_tokens)
        word_assessments = self._build_word_assessments(target_tokens, transcript_tokens)
        weakest_words = [
            assessment["target_word"]
            for assessment in sorted(word_assessments, key=lambda item: item["score"])[:2]
            if assessment["score"] < 75
        ]
        focus_assessments = self._build_focus_assessments(target_tokens, transcript_tokens, target_text, transcript)

        score = round(token_ratio * 100)
        if "th" in target_text.lower():
            if any("th" in token for token in transcript_tokens):
                score = min(100, score + 8)
            else:
                score = max(0, score - 10)
        if weakest_words:
            score = max(0, score - min(12, len(weakest_words) * 4))
        strong_focuses = len([item for item in focus_assessments if item["status"] == "stable"])
        weak_focuses = len([item for item in focus_assessments if item["status"] == "needs_work"])
        score = min(100, score + strong_focuses * 2)
        score = max(0, score - weak_focuses * 3)

        if score >= 85:
            feedback = "Strong match with the target phrase. Keep the same rhythm, stress and clarity."
        elif score >= 65:
            feedback = "Mostly clear. Repeat once more and focus on the weaker words or sound patterns."
        elif score >= 45:
            feedback = "Part of the phrase was recognized, but key sounds or words dropped. Slow down and repeat word by word."
        else:
            feedback = "Recognition was weak. Break the phrase into smaller parts and retry with clearer articulation."

        return {
            "score": score,
            "matched_tokens": matched,
            "missed_tokens": missed,
            "feedback": feedback,
            "weakest_words": weakest_words,
            "word_assessments": word_assessments,
            "focus_assessments": focus_assessments,
        }

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            key="rule_based_scoring",
            name="Rule-Based Scoring",
            type="scoring",
            status=ProviderAvailability.READY,
            details="Rule-based scoring is active for pronunciation and lightweight checkpoint evaluation.",
        )

    @staticmethod
    def _normalize(text: str) -> list[str]:
        return re.findall(r"[a-z']+", text.lower())

    @staticmethod
    def _best_match(target_word: str, transcript_tokens: list[str]) -> tuple[str | None, float]:
        best_word = None
        best_ratio = 0.0
        for token in transcript_tokens:
            ratio = SequenceMatcher(None, target_word, token).ratio()
            if ratio > best_ratio:
                best_word = token
                best_ratio = ratio
        return best_word, best_ratio

    def _build_word_assessments(self, target_tokens: list[str], transcript_tokens: list[str]) -> list[dict[str, object]]:
        assessments: list[dict[str, object]] = []
        for target_word in target_tokens:
            heard_word, ratio = self._best_match(target_word, transcript_tokens)
            score = round(ratio * 100)
            if heard_word == target_word:
                status = "stable"
                note = "Word was recognized clearly."
            elif score >= 70:
                status = "near_match"
                note = "Close match, but pronunciation or articulation still softened part of the word."
            else:
                status = "needs_work"
                note = "This word was weakly recognized. Slow down and exaggerate the stressed sounds."

            assessments.append(
                {
                    "target_word": target_word,
                    "heard_word": heard_word,
                    "score": score,
                    "status": status,
                    "note": note,
                }
            )
        return assessments

    def _build_focus_assessments(
        self,
        target_tokens: list[str],
        transcript_tokens: list[str],
        target_text: str,
        transcript: str,
    ) -> list[dict[str, object]]:
        focus_assessments: list[dict[str, object]] = []
        normalized_target_text = target_text.lower()
        normalized_transcript = transcript.lower()

        if any("th" in token for token in target_tokens):
            focus_assessments.append(
                {
                    "focus": "th",
                    "status": "stable" if any("th" in token for token in transcript_tokens) else "needs_work",
                    "note": "The 'th' sound carried through the phrase."
                    if any("th" in token for token in transcript_tokens)
                    else "The target includes 'th', but it was not heard clearly in the transcript.",
                }
            )

        if any("r" in token for token in target_tokens):
            focus_assessments.append(
                {
                    "focus": "r-coloring",
                    "status": "stable" if "r" in normalized_transcript else "needs_work",
                    "note": "The /r/ sound stayed audible."
                    if "r" in normalized_transcript
                    else "Words with /r/ may be getting softened or dropped.",
                }
            )

        if len(target_tokens) >= 4:
            matched_count = len([token for token in target_tokens if token in transcript_tokens])
            focus_assessments.append(
                {
                    "focus": "word rhythm",
                    "status": "stable" if matched_count >= max(2, len(target_tokens) - 1) else "needs_work",
                    "note": "Most words stayed intact, so sentence rhythm held together."
                    if matched_count >= max(2, len(target_tokens) - 1)
                    else "Several words dropped out, which suggests rhythm or chunking broke down.",
                }
            )

        if normalized_target_text.endswith("ed"):
            focus_assessments.append(
                {
                    "focus": "word ending",
                    "status": "stable" if normalized_transcript.endswith("ed") else "needs_work",
                    "note": "The ending was preserved."
                    if normalized_transcript.endswith("ed")
                    else "The final ending may be disappearing; exaggerate the last consonant.",
                }
            )

        return focus_assessments
