export interface AgentUsage {
  slug: string
  name: string
  conversation_count: number
  message_count: number
}

export interface ModelUsage {
  model_name: string
  tokens: number
  estimated_cost_usd: number
}

export interface DailyUsage {
  date: string
  tokens: number
}

export interface UsageSummary {
  total_tokens: number
  total_messages: number
  estimated_cost_usd: number
  by_model: ModelUsage[]
  daily: DailyUsage[]
}

export interface TaskSummary {
  todo: number
  in_progress: number
  done: number
  overdue: number
  total: number
}

export interface ProjectSummary {
  active: number
  paused: number
  done: number
  archived: number
  total: number
}

export interface McpSummary {
  total: number
  enabled: number
}

export interface SessionSummary {
  terminal_active: number
  browser_active: number
}

export interface DashboardSummary {
  agents: AgentUsage[]
  usage: UsageSummary
  tasks: TaskSummary
  projects: ProjectSummary
  mcp_servers: McpSummary
  sessions: SessionSummary
}

export interface AuditLogEntry {
  id: string
  user_id: string | null
  action: string
  resource_type: string | null
  resource_id: string | null
  log_metadata: Record<string, unknown>
  ip_address: string | null
  created_at: string
}
