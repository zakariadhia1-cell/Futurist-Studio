import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.note import Note
from app.models.user import User
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


async def _get_owned_note(note_id: uuid.UUID, db: AsyncSession, user: User) -> Note:
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notiz nicht gefunden.")
    return note


@router.get("", response_model=list[NoteRead])
async def list_notes(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[NoteRead]:
    result = await db.execute(select(Note).where(Note.user_id == user.id).order_by(Note.updated_at.desc()))
    return [NoteRead.model_validate(n) for n in result.scalars().all()]


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> NoteRead:
    note = Note(user_id=user.id, **payload.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteRead.model_validate(note)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NoteRead:
    note = await _get_owned_note(note_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    await db.commit()
    await db.refresh(note)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    note = await _get_owned_note(note_id, db, user)
    await db.delete(note)
    await db.commit()
