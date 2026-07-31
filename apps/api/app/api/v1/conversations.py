import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import ConversationCreate, ConversationRead, MessageRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ConversationRead]:
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())
    )
    return [ConversationRead.model_validate(c) for c in result.scalars().all()]


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationRead:
    agent_result = await db.execute(select(Agent).where(Agent.slug == payload.agent_slug))
    agent = agent_result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{payload.agent_slug}' nicht gefunden.")

    conversation = Conversation(user_id=user.id, agent_id=agent.id, title=payload.title)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return ConversationRead.model_validate(conversation)


async def _get_owned_conversation(conversation_id: uuid.UUID, db: AsyncSession, user: User) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Konversation nicht gefunden.")
    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MessageRead]:
    await _get_owned_conversation(conversation_id, db, user)
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    return [MessageRead.model_validate(m) for m in result.scalars().all()]
