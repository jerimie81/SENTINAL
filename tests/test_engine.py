from flash_ai.engine import FlashcardEngine, GenerationConfig
from flash_ai.service import FlashAIService


def test_engine_generates_cards_from_long_sentences() -> None:
    engine = FlashcardEngine(GenerationConfig(max_cards=2, min_sentence_length=20))
    source = (
        "Flash-AI converts documents into bite-sized cards for rapid study. "
        "Each card is generated using deterministic starter logic before LLM integration."
    )

    cards = engine.generate(source)

    assert len(cards) == 2
    assert all("_____" in card.question for card in cards)
    assert all(card.answer for card in cards)


def test_service_persists_deck_in_memory() -> None:
    service = FlashAIService()
    deck = service.create_deck(
        title="Intro",
        source_text="This sentence is long enough to produce at least one generated flashcard.",
    )

    loaded = service.get_deck(deck.id)

    assert loaded is not None
    assert loaded.title == "Intro"
    assert loaded.cards
