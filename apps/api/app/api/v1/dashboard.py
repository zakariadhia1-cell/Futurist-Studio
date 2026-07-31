"""Aggregated read-only summary for the dashboard - one round trip instead of the
frontend fanning out to a dozen endpoints and stitching results together itself.
Every query is scoped to the calling user's own data (conversations, tasks, projects,
MCP servers, live sessions) - same ownership model as the rest of the API, see
core/dependencies.py."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.live import browser_manager, terminal_manager
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.mcp_server import McpServer
from app.models.message import Message
from app.models.model_config import ModelConfig
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.dashboard import (
    AgentUsageRead,
    DailyUsageRead,
    DashboardSummaryRead,
    McpSummaryRead,
    ModelUsageRead,
    ProjectSummaryRead,
    SessionSummaryRead,
    TaskSummaryRead,
    UsageSummaryRead,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_USAGE_WINDOW_DAYS = 14


async def _agent_usage(db: AsyncSession, user: User) -> list[AgentUsageRead]:
    result = await db.execute(
        select(
            Agent.slug,
            Agent.name,
            func.count(func.distinct(Conversation.id)),
            func.count(Message.id),
        )
        .select_from(Agent)
        .outerjoin(
            Conversation, (Conversation.agent_id == Agent.id) & (Conversation.user_id == user.id)
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Agent.enabled.is_(True))
        .group_by(Agent.id)
        .order_by(Agent.name)
    )
    return [
        AgentUsageRead(slug=slug, name=name, conversation_count=conv_count, message_count=msg_count)
        for slug, name, conv_count, msg_count in result.all()
    ]


async def _usage_summary(db: AsyncSession, user: User) -> UsageSummaryRead:
    totals = await db.execute(
        select(func.coalesce(func.sum(Message.tokens_used), 0), func.count(Message.id))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == user.id, Message.tokens_used.is_not(None))
    )
    total_tokens, total_messages = totals.one()

    by_model_rows = await db.execute(
        select(Message.model_used, func.sum(Message.tokens_used))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Conversation.user_id == user.id,
            Message.tokens_used.is_not(None),
            Message.model_used.is_not(None),
        )
        .group_by(Message.model_used)
    )
    model_configs = {mc.model_name: mc for mc in (await db.execute(select(ModelConfig))).scalars().all()}

    by_model: list[ModelUsageRead] = []
    estimated_cost_total = 0.0
    for model_name, tokens in by_model_rows.all():
        tokens = int(tokens or 0)
        config = model_configs.get(model_name)
        # Message only stores a combined tokens_used, not an input/output split, so an
        # exact cost isn't possible - averaging the two per-1k rates is a reasonable
        # estimate for a dashboard, not a billing-accurate figure.
        cost = 0.0
        if config is not None and config.cost_per_1k_input is not None and config.cost_per_1k_output is not None:
            avg_rate = (float(config.cost_per_1k_input) + float(config.cost_per_1k_output)) / 2
            cost = (tokens / 1000) * avg_rate
        estimated_cost_total += cost
        by_model.append(ModelUsageRead(model_name=model_name, tokens=tokens, estimated_cost_usd=round(cost, 4)))
    by_model.sort(key=lambda m: m.tokens, reverse=True)

    since = datetime.now(timezone.utc) - timedelta(days=_USAGE_WINDOW_DAYS)
    daily_rows = await db.execute(
        select(func.date(Message.created_at), func.coalesce(func.sum(Message.tokens_used), 0))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == user.id, Message.created_at >= since)
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
    )
    daily = [DailyUsageRead(date=day, tokens=int(tokens)) for day, tokens in daily_rows.all()]

    return UsageSummaryRead(
        total_tokens=int(total_tokens or 0),
        total_messages=int(total_messages or 0),
        estimated_cost_usd=round(estimated_cost_total, 4),
        by_model=by_model,
        daily=daily,
    )


async def _task_summary(db: AsyncSession, user: User) -> TaskSummaryRead:
    rows = await db.execute(select(Task.status, func.count(Task.id)).where(Task.user_id == user.id).group_by(Task.status))
    counts = {status: count for status, count in rows.all()}
    overdue_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.user_id == user.id,
            Task.status != "done",
            Task.due_date.is_not(None),
            Task.due_date < datetime.now(timezone.utc),
        )
    )
    overdue = overdue_result.scalar_one()
    return TaskSummaryRead(
        todo=counts.get("todo", 0),
        in_progress=counts.get("in_progress", 0),
        done=counts.get("done", 0),
        overdue=overdue,
        total=sum(counts.values()),
    )


async def _project_summary(db: AsyncSession, user: User) -> ProjectSummaryRead:
    rows = await db.execute(
        select(Project.status, func.count(Project.id)).where(Project.user_id == user.id).group_by(Project.status)
    )
    counts = {status: count for status, count in rows.all()}
    return ProjectSummaryRead(
        active=counts.get("active", 0),
        paused=counts.get("paused", 0),
        done=counts.get("done", 0),
        archived=counts.get("archived", 0),
        total=sum(counts.values()),
    )


async def _mcp_summary(db: AsyncSession, user: User) -> McpSummaryRead:
    result = await db.execute(select(McpServer.enabled).where(McpServer.user_id == user.id))
    flags = result.scalars().all()
    return McpSummaryRead(total=len(flags), enabled=sum(1 for f in flags if f))


@router.get("/summary", response_model=DashboardSummaryRead)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> DashboardSummaryRead:
    return DashboardSummaryRead(
        agents=await _agent_usage(db, user),
        usage=await _usage_summary(db, user),
        tasks=await _task_summary(db, user),
        projects=await _project_summary(db, user),
        mcp_servers=await _mcp_summary(db, user),
        sessions=SessionSummaryRead(
            terminal_active=len(terminal_manager.list_sessions(user.id)),
            browser_active=len(browser_manager.list_sessions(user.id)),
        ),
    )
