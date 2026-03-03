from __future__ import annotations

from .engine import FlashcardEngine
from .models import Deck


class FlashAIService:
    def __init__(self, engine: FlashcardEngine | None = None) -> None:
        self._engine = engine or FlashcardEngine()
        self._decks: dict[str, Deck] = {}

    def create_deck(self, title: str, source_text: str) -> Deck:
        cards = self._engine.generate(source_text)
        deck = Deck(title=title, source_text=source_text, cards=cards)
        self._decks[deck.id] = deck
        return deck

    def get_deck(self, deck_id: str) -> Deck | None:
        return self._decks.get(deck_id)
