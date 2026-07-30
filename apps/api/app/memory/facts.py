import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory_fact import MemoryFact
from app.models_provider.embeddings import EmbeddingProvider
from app.models_provider.registry import get_embedding_provider


async def add_memory_fact(
    db: AsyncSession,
    user_id: uuid.UUID,
    subject: str,
    fact_text: str,
    source: str | None = None,
    confidence: float = 1.0,
    embedding_provider: EmbeddingProvider | None = None,
) -> MemoryFact:
    provider = embedding_provider or get_embedding_provider()
    [embedding] = await provider.embed([f"{subject}: {fact_text}"])

    fact = MemoryFact(
        user_id=user_id,
        subject=subject,
        fact_text=fact_text,
        source=source,
        confidence=confidence,
        embedding=embedding,
    )
    db.add(fact)
    await db.commit()
    await db.refresh(fact)
    return fact
