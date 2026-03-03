from sentinal import Document, HashEmbedder, KnowledgeBase, RetrievalConfig, RetrievalQAService


def test_add_document_creates_chunks_and_is_searchable() -> None:
    kb = KnowledgeBase(embedder=HashEmbedder(dimensions=32), config=RetrievalConfig(chunk_size=8, chunk_overlap=2, top_k=3))
    content = (
        "SENTINAL is a portable offline AI assistant designed for resilient environments. "
        "It uses local indexing and retrieval to answer questions without internet access."
    )
    document = Document(title="Overview", content=content)

    chunk_count = kb.add_document(document)
    results = kb.search("How does SENTINAL answer questions?")

    assert chunk_count > 0
    assert kb.document_count == 1
    assert results
    assert len(results) <= 3


def test_qa_service_returns_citations() -> None:
    kb = KnowledgeBase(embedder=HashEmbedder(dimensions=16), config=RetrievalConfig(chunk_size=6, chunk_overlap=1, top_k=2))
    kb.add_document(
        Document(
            title="Architecture",
            content="SENTINAL includes document ingestion, vector indexing, and retrieval QA components.",
        )
    )

    answer = RetrievalQAService(kb).answer("What components does SENTINAL include?")

    assert answer.text
    assert answer.citations
