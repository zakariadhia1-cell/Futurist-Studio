from datetime import date

from pydantic import BaseModel


class AgentUsageRead(BaseModel):
    slug: str
    name: str
    conversation_count: int
    message_count: int


class ModelUsageRead(BaseModel):
    model_name: str
    tokens: int
    estimated_cost_usd: float


class DailyUsageRead(BaseModel):
    date: date
    tokens: int


class UsageSummaryRead(BaseModel):
    total_tokens: int
    total_messages: int
    estimated_cost_usd: float
    by_model: list[ModelUsageRead]
    daily: list[DailyUsageRead]


class TaskSummaryRead(BaseModel):
    todo: int
    in_progress: int
    done: int
    overdue: int
    total: int


class ProjectSummaryRead(BaseModel):
    active: int
    paused: int
    done: int
    archived: int
    total: int


class McpSummaryRead(BaseModel):
    total: int
    enabled: int


class SessionSummaryRead(BaseModel):
    terminal_active: int
    browser_active: int


class DashboardSummaryRead(BaseModel):
    agents: list[AgentUsageRead]
    usage: UsageSummaryRead
    tasks: TaskSummaryRead
    projects: ProjectSummaryRead
    mcp_servers: McpSummaryRead
    sessions: SessionSummaryRead
