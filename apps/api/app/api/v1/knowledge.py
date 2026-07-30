import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.memory.ingestion import ingest_document
from app.memory.search import search_documents
from app.models.document import Document
from app.models.user import User
from app.schemas.knowledge import (
    DocumentCreate,
    DocumentDetail,
    DocumentRead,
    SearchChunkResult,
    SearchRequest,
    SearchResponse,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[DocumentRead]:
    result = await db.execute(
        select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
    )
    return [DocumentRead.model_validate(d) for d in result.scalars().all()]


@router.post("/documents", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentDetail:
    document = await ingest_document(
        db, user_id=user.id, title=payload.title, content=payload.content, source_type=payload.source_type
    )
    return DocumentDetail.model_validate(document)


async def _get_owned_document(document_id: uuid.UUID, db: AsyncSession, user: User) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden.")
    return document


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> DocumentDetail:
    document = await _get_owned_document(document_id, db, user)
    return DocumentDetail.model_validate(document)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    document = await _get_owned_document(document_id, db, user)
    await db.delete(document)
    await db.commit()


@router.post("/search", response_model=SearchResponse)
async def search(
    payload: SearchRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> SearchResponse:
    results = await search_documents(db, user.id, payload.query, top_k=payload.top_k)
    return SearchResponse(
        results=[
            SearchChunkResult(
                document_id=r.document_id, document_title=r.document_title, content=r.content, distance=r.distance
            )
            for r in results
        ]
    )
