from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List

from .models import Flashcard


@dataclass(slots=True)
class GenerationConfig:
    max_cards: int = 10
    min_sentence_length: int = 30


class FlashcardEngine:
    """Rule-based starter engine.

    This is intentionally deterministic so it can be replaced by an LLM-backed
    implementation once provider integration is available.
    """

    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()

    def generate(self, source_text: str) -> List[Flashcard]:
        sentences = list(self._candidate_sentences(source_text))
        cards: List[Flashcard] = []

        for sentence in sentences[: self.config.max_cards]:
            answer = self._extract_answer(sentence)
            question = sentence.replace(answer, "_____", 1)
            cards.append(Flashcard(question=question, answer=answer, tags=["auto-generated"]))

        return cards

    def _candidate_sentences(self, source_text: str) -> Iterable[str]:
        for raw_sentence in re.split(r"(?<=[.!?])\s+", source_text.strip()):
            sentence = raw_sentence.strip()
            if len(sentence) >= self.config.min_sentence_length:
                yield sentence

    @staticmethod
    def _extract_answer(sentence: str) -> str:
        words = re.findall(r"[A-Za-z0-9'-]+", sentence)
        if not words:
            return ""
        midpoint = min(len(words) - 1, max(0, len(words) // 2))
        return words[midpoint]
