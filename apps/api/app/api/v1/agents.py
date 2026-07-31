from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agent import AgentRead

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
async def list_agents(
    db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)
) -> list[AgentRead]:
    result = await db.execute(select(Agent).where(Agent.enabled.is_(True)).order_by(Agent.name))
    return [AgentRead.from_model(a) for a in result.scalars().all()]
