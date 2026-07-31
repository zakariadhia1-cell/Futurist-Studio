import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source_type: str = "note"


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source_type: str
    created_at: datetime


class DocumentDetail(DocumentRead):
    content_text: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchChunkResult(BaseModel):
    document_id: uuid.UUID
    document_title: str
    content: str
    distance: float


class SearchResponse(BaseModel):
    results: list[SearchChunkResult]
