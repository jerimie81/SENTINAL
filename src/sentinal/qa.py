from __future__ import annotations

from dataclasses import dataclass

from .knowledge_base import KnowledgeBase


@dataclass(slots=True)
class Answer:
    text: str
    citations: list[str]


class RetrievalQAService:
    """Offline-first retrieval QA bootstrap service."""

    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def answer(self, question: str) -> Answer:
        results = self.kb.search(question)
        if not results:
            return Answer(
                text="I could not find relevant knowledge in the local store yet.",
                citations=[],
            )

        snippets = [res.chunk.content for res in results]
        summary = " ".join(snippets[:2])
        citations = [f"{res.chunk.document_id}#{res.chunk.index}" for res in results]
        return Answer(text=summary, citations=citations)
