import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.memory_fact import MemoryFact
from app.models_provider.embeddings import EmbeddingProvider
from app.models_provider.registry import get_embedding_provider


@dataclass
class ChunkResult:
    document_id: uuid.UUID
    document_title: str
    content: str
    distance: float  # cosine distance: 0 = identical, 2 = opposite


@dataclass
class FactResult:
    fact_id: uuid.UUID
    subject: str
    fact_text: str
    distance: float


async def search_documents(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    top_k: int = 5,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[ChunkResult]:
    provider = embedding_provider or get_embedding_provider()
    [query_embedding] = await provider.embed([query])

    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(DocumentChunk, Document.title, distance.label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.user_id == user_id)
        .order_by(distance)
        .limit(top_k)
    )
    rows = (await db.execute(stmt)).all()
    return [
        ChunkResult(document_id=chunk.document_id, document_title=title, content=chunk.content, distance=dist)
        for chunk, title, dist in rows
    ]


_RELEVANCE_THRESHOLD = 0.9  # cosine distance; below this, treat a result as relevant enough to surface


def build_memory_context(chunks: list[ChunkResult], facts: list[FactResult]) -> str | None:
    """Renders retrieved chunks/facts into a system-prompt block, or None if nothing
    was relevant enough to bother the model with."""
    relevant_chunks = [c for c in chunks if c.distance < _RELEVANCE_THRESHOLD]
    relevant_facts = [f for f in facts if f.distance < _RELEVANCE_THRESHOLD]
    if not relevant_chunks and not relevant_facts:
        return None

    lines = ["Relevanter Kontext aus dem Gedaechtnis (nutze ihn nur, wenn er zur Frage passt):"]
    for fact in relevant_facts:
        lines.append(f"- [Fakt] {fact.subject}: {fact.fact_text}")
    for chunk in relevant_chunks:
        lines.append(f"- [Aus '{chunk.document_title}'] {chunk.content}")
    return "\n".join(lines)


async def search_memory_facts(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    top_k: int = 5,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[FactResult]:
    provider = embedding_provider or get_embedding_provider()
    [query_embedding] = await provider.embed([query])

    distance = MemoryFact.embedding.cosine_distance(query_embedding)
    stmt = (
        select(MemoryFact, distance.label("distance"))
        .where(MemoryFact.user_id == user_id)
        .order_by(distance)
        .limit(top_k)
    )
    rows = (await db.execute(stmt)).all()
    return [
        FactResult(fact_id=fact.id, subject=fact.subject, fact_text=fact.fact_text, distance=dist)
        for fact, dist in rows
    ]
