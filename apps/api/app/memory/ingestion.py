import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.chunking import chunk_text
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models_provider.embeddings import EmbeddingProvider
from app.models_provider.registry import get_embedding_provider


async def ingest_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    content: str,
    source_type: str = "note",
    embedding_provider: EmbeddingProvider | None = None,
) -> Document:
    """Store a document and its embedded chunks. Commits the transaction."""
    provider = embedding_provider or get_embedding_provider()

    document = Document(user_id=user_id, title=title, source_type=source_type, content_text=content)
    db.add(document)
    await db.flush()  # assigns document.id

    pieces = chunk_text(content)
    if pieces:
        embeddings = await provider.embed(pieces)
        for index, (piece, embedding) in enumerate(zip(pieces, embeddings)):
            db.add(DocumentChunk(document_id=document.id, chunk_index=index, content=piece, embedding=embedding))

    await db.commit()
    await db.refresh(document)
    return document
