import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_owned_task(task_id: uuid.UUID, db: AsyncSession, user: User) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden.")
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[TaskRead]:
    result = await db.execute(select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc()))
    return [TaskRead.model_validate(t) for t in result.scalars().all()]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> TaskRead:
    task = Task(user_id=user.id, **payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskRead:
    task = await _get_owned_task(task_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    task = await _get_owned_task(task_id, db, user)
    await db.delete(task)
    await db.commit()
