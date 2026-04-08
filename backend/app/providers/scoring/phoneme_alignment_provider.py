from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.providers.scoring.base import BaseScoringProvider
from app.providers.scoring.rule_based_provider import RuleBasedScoringProvider
from app.schemas.provider import ProviderAvailability, ProviderStatus

class PhonemeAlignmentScoringProvider(BaseScoringProvider):
    _COMPOUND_IPA_TOKENS = (
        "tʃ",
        "dʒ",
        "oʊ",
        "aɪ",
        "aʊ",
        "eɪ",
        "ɔɪ",
        "iː",
        "uː",
        "ɑː",
        "ɜː",
    )
    _ARPABET_TO_IPA = {
        "AA": "ɑː",
        "AE": "æ",
        "AO": "ɔ",
        "AW": "aʊ",
        "AY": "aɪ",
        "B": "b",
        "CH": "tʃ",
        "D": "d",
        "DH": "ð",
        "EH": "ɛ",
        "EY": "eɪ",
        "F": "f",
        "G": "ɡ",
        "HH": "h",
        "IH": "ɪ",
        "IY": "iː",
        "JH": "dʒ",
        "K": "k",
        "L": "l",
        "M": "m",
        "N": "n",
        "NG": "ŋ",
        "OW": "oʊ",
        "OY": "ɔɪ",
        "P": "p",
        "R": "ɹ",
        "S": "s",
        "SH": "ʃ",
        "T": "t",
        "TH": "θ",
        "UH": "ʊ",
        "UW": "uː",
        "V": "v",
        "W": "w",
        "Y": "j",
        "Z": "z",
        "ZH": "ʒ",
    }

    def __init__(self, fallback_provider: RuleBasedScoringProvider | None = None) -> None:
        self._fallback_provider = fallback_provider or RuleBasedScoringProvider()
        self._model: Any | None = None
        self._feature_extractor: Any | None = None
        self._vocab: dict[str, int] | None = None

    def score(self, content: str) -> int:
        return self._fallback_provider.score(content)

    def score_pronunciation(
        self,
        target_text: str,
        transcript: str,
        acoustic_signals: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if not settings.pronunciation_alignment_enabled:
            return self._fallback_provider.score_pronunciation(target_text, transcript, acoustic_signals)

        audio_path_value = (acoustic_signals or {}).get("audio_path")
        audio_path = Path(str(audio_path_value)).expanduser() if audio_path_value else None
        if audio_path is None or not audio_path.exists():
            return self._fallback_provider.score_pronunciation(target_text, transcript, acoustic_signals)

        try:
            aligned = self._align_and_score(audio_path, target_text=target_text, transcript=transcript)
        except Exception:
            aligned = None

        if aligned is None:
            return self._fallback_provider.score_pronunciation(target_text, transcript, acoustic_signals)
        return aligned

    def status(self) -> ProviderStatus:
        if not settings.pronunciation_alignment_enabled:
            return ProviderStatus(
                key="phoneme_alignment_scoring",
                name="Phoneme Alignment Scoring",
                type="scoring",
                status=ProviderAvailability.READY,
                details="Phoneme alignment is disabled in configuration. Rule-based pronunciation scoring is active.",
            )

        try:
            self._import_runtime_dependencies()
        except Exception as exc:
            return ProviderStatus(
                key="phoneme_alignment_scoring",
                name="Phoneme Alignment Scoring",
                type="scoring",
                status=ProviderAvailability.READY,
                details=f"Forced alignment runtime is unavailable ({exc}). Rule-based pronunciation scoring will be used as a fallback.",
            )

        return ProviderStatus(
            key="phoneme_alignment_scoring",
            name="Phoneme Alignment Scoring",
            type="scoring",
            status=ProviderAvailability.READY,
            details=(
                f"Uses local phoneme-level forced alignment via '{settings.pronunciation_alignment_model}' "
                "with rule-based fallback when alignment data is unavailable."
            ),
        )

    def _align_and_score(self, audio_path: Path, *, target_text: str, transcript: str) -> dict[str, object] | None:
        word_targets = self._build_word_targets(target_text)
        if not word_targets:
            return None

        phone_tokens = [token for _, phones in word_targets for token in phones]
        if len(phone_tokens) < 2:
            return None

        emissions = self._build_emissions(audio_path)
        vocab = self._get_vocab()
        blank_id = vocab["<pad>"]
        try:
            token_ids = [vocab[token] for token in phone_tokens]
        except KeyError:
            return None

        anchors = self._forced_align(emissions, token_ids, blank_id)
        if anchors is None or len(anchors) != len(phone_tokens):
            return None

        phone_scores = self._score_aligned_phones(emissions, token_ids, anchors)
        word_assessments = self._build_word_assessments(word_targets, phone_scores, transcript)
        if not word_assessments:
            return None

        transcript_tokens = self._normalize_text(transcript)
        target_tokens = [word for word, _ in word_targets]
        matched_tokens = [token for token in target_tokens if token in transcript_tokens]
        missed_tokens = [token for token in target_tokens if token not in transcript_tokens]
        token_ratio = len(matched_tokens) / len(target_tokens) if target_tokens else 0.0
        average_word_score = sum(int(item["score"]) for item in word_assessments) / len(word_assessments)
        score = round(average_word_score * 0.9 + token_ratio * 15)
        if not missed_tokens:
            score += 6

        weakest_words = [
            item["target_word"]
            for item in sorted(word_assessments, key=lambda item: int(item["score"]))[:2]
            if int(item["score"]) < 78
        ]
        focus_assessments = self._build_focus_assessments(phone_scores, transcript_tokens, weakest_words)
        strong_focuses = len([item for item in focus_assessments if item["status"] == "stable"])
        weak_focuses = len([item for item in focus_assessments if item["status"] == "needs_work"])
        score = min(100, score + strong_focuses * 2)
        score = max(0, score - weak_focuses * 2)

        if score >= 85:
            feedback = "Phoneme alignment looks strong. The phrase stayed clear and stable across most sounds."
        elif score >= 65:
            feedback = "Mostly clear. A few sounds softened, but the phrase was still easy to follow."
        elif score >= 45:
            feedback = "Partly clear. Several sounds blurred together, so slow down and stress the key words."
        else:
            feedback = "The phrase was hard to track at the phoneme level. Try chunking it into smaller parts."

        return {
            "score": score,
            "matched_tokens": matched_tokens,
            "missed_tokens": missed_tokens,
            "feedback": feedback,
            "weakest_words": weakest_words,
            "word_assessments": word_assessments,
            "focus_assessments": focus_assessments,
        }

    def _build_word_targets(self, text: str) -> list[tuple[str, list[str]]]:
        word_targets: list[tuple[str, list[str]]] = []
        missing_words = 0
        words = self._normalize_text(text)
        for word in words:
            phones = self._word_to_ipa_tokens(word)
            if not phones:
                missing_words += 1
                continue
            word_targets.append((word, phones))

        if not word_targets:
            return []

        missing_ratio = missing_words / max(1, len(words))
        if missing_ratio > 0.4:
            return []
        return word_targets

    def _word_to_ipa_tokens(self, word: str) -> list[str]:
        pronouncing = self._import_runtime_dependencies()["pronouncing"]
        pronunciations = pronouncing.phones_for_word(word)
        if not pronunciations and word.endswith("'d"):
            pronunciations = pronouncing.phones_for_word(word[:-2])
        if not pronunciations:
            return []

        vocab = self._get_vocab()
        tokens: list[str] = []
        for arpabet_phone in pronunciations[0].split():
            ipa_value = self._arpabet_phone_to_ipa(arpabet_phone)
            if not ipa_value:
                continue
            for token in self._split_ipa_tokens(ipa_value):
                if token in vocab:
                    tokens.append(token)
        return tokens

    def _build_emissions(self, audio_path: Path):
        runtime = self._import_runtime_dependencies()
        numpy = runtime["numpy"]
        soundfile = runtime["soundfile"]
        torch = runtime["torch"]

        waveform, sample_rate = soundfile.read(str(audio_path))
        if getattr(waveform, "ndim", 1) > 1:
            waveform = waveform.mean(axis=1)
        waveform = numpy.asarray(waveform, dtype=numpy.float32)
        if sample_rate != 16000:
            source_positions = numpy.arange(len(waveform), dtype=numpy.float32)
            target_length = int(round((len(waveform) / sample_rate) * 16000))
            target_positions = numpy.linspace(0, len(waveform) - 1, num=target_length, dtype=numpy.float32)
            waveform = numpy.interp(target_positions, source_positions, waveform).astype(numpy.float32)

        feature_extractor = self._get_feature_extractor()
        model = self._get_model()
        inputs = feature_extractor(waveform, sampling_rate=16000, return_tensors="pt")
        if self._resolve_device() == "cuda":
            inputs = {key: value.to("cuda") for key, value in inputs.items()}
            model = model.to("cuda")
        with torch.no_grad():
            logits = model(**inputs).logits[0]
        return torch.log_softmax(logits.detach().cpu(), dim=-1)

    def _forced_align(self, emissions, token_ids: list[int], blank_id: int) -> list[int] | None:
        torch = self._import_runtime_dependencies()["torch"]

        frame_count = int(emissions.size(0))
        token_count = len(token_ids)
        trellis = torch.full((frame_count + 1, token_count + 1), -float("inf"))
        trellis[0, 0] = 0.0

        for frame_index in range(frame_count):
            trellis[frame_index + 1, 0] = trellis[frame_index, 0] + emissions[frame_index, blank_id]
            stay_scores = trellis[frame_index, 1:] + emissions[frame_index, blank_id]
            change_scores = trellis[frame_index, :-1] + emissions[frame_index, token_ids]
            trellis[frame_index + 1, 1:] = torch.maximum(stay_scores, change_scores)

        frame_index = int(torch.argmax(trellis[:, token_count]).item())
        token_index = token_count
        anchors: list[tuple[int, int]] = []

        while token_index > 0 and frame_index > 0:
            stay_score = trellis[frame_index - 1, token_index] + emissions[frame_index - 1, blank_id]
            change_score = trellis[frame_index - 1, token_index - 1] + emissions[frame_index - 1, token_ids[token_index - 1]]
            if change_score > stay_score:
                anchors.append((token_index - 1, frame_index - 1))
                token_index -= 1
            frame_index -= 1

        if token_index != 0:
            return None

        anchors.reverse()
        return [frame for _, frame in anchors]

    def _score_aligned_phones(self, emissions, token_ids: list[int], anchors: list[int]) -> list[dict[str, object]]:
        torch = self._import_runtime_dependencies()["torch"]
        vocab = self._get_vocab()
        id_to_token = {value: key for key, value in vocab.items()}
        scores: list[dict[str, object]] = []
        total_frames = int(emissions.size(0))

        for token_index, anchor in enumerate(anchors):
            start_frame = max(0, anchor - 1)
            end_frame = min(total_frames - 1, anchor + 1)
            token_id = token_ids[token_index]
            local_probabilities = torch.exp(emissions[start_frame : end_frame + 1, token_id])
            confidence = float(local_probabilities.max().item())
            calibrated_score = int(round(max(0.0, min(1.0, confidence)) ** 0.3 * 100))
            scores.append(
                {
                    "token": id_to_token.get(token_id, ""),
                    "index": token_index,
                    "frame": anchor,
                    "confidence": confidence,
                    "score": calibrated_score,
                }
            )
        return scores

    def _build_word_assessments(
        self,
        word_targets: list[tuple[str, list[str]]],
        phone_scores: list[dict[str, object]],
        transcript: str,
    ) -> list[dict[str, object]]:
        transcript_tokens = self._normalize_text(transcript)
        assessments: list[dict[str, object]] = []
        cursor = 0

        for word, phones in word_targets:
            next_cursor = cursor + len(phones)
            current_phone_scores = phone_scores[cursor:next_cursor]
            cursor = next_cursor
            if not current_phone_scores:
                continue

            average_score = round(
                sum(int(item["score"]) for item in current_phone_scores) / len(current_phone_scores)
            )
            if average_score >= 85:
                status = "stable"
                note = "Phoneme alignment stayed stable across this word."
            elif average_score >= 65:
                status = "near_match"
                note = "Most sounds landed well, but one part of the word softened."
            else:
                status = "needs_work"
                note = "Several sounds in this word were weak or blurred together."

            assessments.append(
                {
                    "target_word": word,
                    "heard_word": word if word in transcript_tokens else self._best_match(word, transcript_tokens),
                    "score": average_score,
                    "status": status,
                    "note": note,
                }
            )

        return assessments

    def _build_focus_assessments(
        self,
        phone_scores: list[dict[str, object]],
        transcript_tokens: list[str],
        weakest_words: list[str],
    ) -> list[dict[str, object]]:
        focus_items: list[dict[str, object]] = []

        th_scores = [item["score"] for item in phone_scores if item["token"] in {"θ", "ð"}]
        if th_scores:
            average = sum(int(score) for score in th_scores) / len(th_scores)
            focus_items.append(
                {
                    "focus": "th",
                    "status": "stable" if average >= 72 else "needs_work",
                    "note": "The /th/ sound stayed distinct." if average >= 72 else "The /th/ sound softened and needs clearer tongue placement.",
                }
            )

        r_scores = [item["score"] for item in phone_scores if item["token"] in {"ɹ", "r"}]
        if r_scores:
            average = sum(int(score) for score in r_scores) / len(r_scores)
            focus_items.append(
                {
                    "focus": "r-coloring",
                    "status": "stable" if average >= 72 else "needs_work",
                    "note": "The /r/ sound stayed audible." if average >= 72 else "The /r/ sound is getting softened or lost.",
                }
            )

        average_phone_score = sum(int(item["score"]) for item in phone_scores) / max(1, len(phone_scores))
        focus_items.append(
            {
                "focus": "word rhythm",
                "status": "stable" if average_phone_score >= 68 and len(transcript_tokens) >= 3 else "needs_work",
                "note": "The phrase stayed connected and easy to follow."
                if average_phone_score >= 68 and len(transcript_tokens) >= 3
                else "The phrase lost flow, so the rhythm needs to be more connected.",
            }
        )

        if phone_scores:
            last_score = int(phone_scores[-1]["score"])
            focus_items.append(
                {
                    "focus": "word ending",
                    "status": "stable" if last_score >= 65 else "needs_work",
                    "note": "The ending sound carried through." if last_score >= 65 else "The ending sound faded out too early.",
                }
            )

        if weakest_words and not focus_items:
            focus_items.append(
                {
                    "focus": "word rhythm",
                    "status": "needs_work",
                    "note": "A few words still need clearer shaping inside the phrase.",
                }
            )

        return focus_items

    @staticmethod
    def _normalize_text(text: str) -> list[str]:
        return re.findall(r"[a-z']+", text.lower())

    @staticmethod
    def _best_match(target_word: str, transcript_tokens: list[str]) -> str | None:
        if not transcript_tokens:
            return None
        best_word = None
        best_ratio = 0.0
        for token in transcript_tokens:
            ratio = sum(1 for left, right in zip(target_word, token) if left == right) / max(len(target_word), len(token))
            if ratio > best_ratio:
                best_ratio = ratio
                best_word = token
        return best_word

    def _arpabet_phone_to_ipa(self, arpabet_phone: str) -> str | None:
        stress = arpabet_phone[-1] if arpabet_phone and arpabet_phone[-1].isdigit() else None
        base_phone = re.sub(r"\d", "", arpabet_phone)
        if base_phone == "AH" and stress == "0":
            return "ə"
        if base_phone == "ER" and stress == "0":
            return "ə"
        if base_phone == "ER":
            return "ɜː"
        return self._ARPABET_TO_IPA.get(base_phone)

    def _split_ipa_tokens(self, ipa_value: str) -> list[str]:
        tokens: list[str] = []
        cursor = 0
        while cursor < len(ipa_value):
            matched = None
            for token in self._COMPOUND_IPA_TOKENS:
                if ipa_value.startswith(token, cursor):
                    matched = token
                    break
            if matched is not None:
                tokens.append(matched)
                cursor += len(matched)
                continue
            tokens.append(ipa_value[cursor])
            cursor += 1
        return tokens

    def _get_model(self):
        if self._model is not None:
            return self._model

        runtime = self._import_runtime_dependencies()
        model = runtime["AutoModelForCTC"].from_pretrained(settings.pronunciation_alignment_model)
        model.eval()
        self._model = model
        return self._model

    def _get_feature_extractor(self):
        if self._feature_extractor is not None:
            return self._feature_extractor

        runtime = self._import_runtime_dependencies()
        self._feature_extractor = runtime["AutoFeatureExtractor"].from_pretrained(settings.pronunciation_alignment_model)
        return self._feature_extractor

    def _get_vocab(self) -> dict[str, int]:
        if self._vocab is not None:
            return self._vocab

        runtime = self._import_runtime_dependencies()
        vocab_path = runtime["hf_hub_download"](settings.pronunciation_alignment_model, "vocab.json")
        import json

        with open(vocab_path, "r", encoding="utf-8") as vocab_file:
            self._vocab = json.load(vocab_file)
        return self._vocab

    @staticmethod
    @lru_cache(maxsize=1)
    def _import_runtime_dependencies() -> dict[str, Any]:
        import numpy
        import pronouncing
        import soundfile
        import torch
        from huggingface_hub import hf_hub_download
        from transformers import AutoFeatureExtractor, AutoModelForCTC

        return {
            "numpy": numpy,
            "pronouncing": pronouncing,
            "soundfile": soundfile,
            "torch": torch,
            "hf_hub_download": hf_hub_download,
            "AutoFeatureExtractor": AutoFeatureExtractor,
            "AutoModelForCTC": AutoModelForCTC,
        }

    def _resolve_device(self) -> str:
        requested_device = settings.pronunciation_alignment_device.lower()
        if requested_device != "auto":
            return requested_device

        try:
            torch = self._import_runtime_dependencies()["torch"]
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"
