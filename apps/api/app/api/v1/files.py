import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileRead

router = APIRouter(prefix="/files", tags=["files"])


def _user_files_dir(user_id: uuid.UUID) -> str:
    settings = get_settings()
    path = os.path.join(settings.FILES_DIR, str(user_id))
    os.makedirs(path, exist_ok=True)
    return path


async def _get_owned_file(file_id: uuid.UUID, db: AsyncSession, user: User) -> File:
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if file is None or file.user_id != user.id:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")
    return file


@router.get("", response_model=list[FileRead])
async def list_files(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[FileRead]:
    result = await db.execute(select(File).where(File.user_id == user.id).order_by(File.created_at.desc()))
    return [FileRead.model_validate(f) for f in result.scalars().all()]


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    upload: UploadFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileRead:
    settings = get_settings()
    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Datei ist leer.")
    if len(contents) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Datei ist zu gross.")

    storage_key = uuid.uuid4().hex
    dest = os.path.join(_user_files_dir(user.id), storage_key)
    with open(dest, "wb") as f:
        f.write(contents)

    file = File(
        user_id=user.id,
        filename=upload.filename or storage_key,
        content_type=upload.content_type or "application/octet-stream",
        size_bytes=len(contents),
        storage_key=storage_key,
        source="upload",
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return FileRead.model_validate(file)


@router.get("/{file_id}/download")
async def download_file(
    file_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> FileResponse:
    file = await _get_owned_file(file_id, db, user)
    path = os.path.join(_user_files_dir(user.id), file.storage_key)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Datei nicht mehr auf dem Datentraeger vorhanden.")
    return FileResponse(path, media_type=file.content_type, filename=file.filename)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    file = await _get_owned_file(file_id, db, user)
    path = os.path.join(_user_files_dir(user.id), file.storage_key)
    if os.path.isfile(path):
        os.remove(path)
    await db.delete(file)
    await db.commit()
