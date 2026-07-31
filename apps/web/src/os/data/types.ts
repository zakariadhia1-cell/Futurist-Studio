/** Shared types for the OS control center. Every list here mirrors the shape a real
 * backend endpoint would return, so swapping mock.ts for real `api.get<T>(...)` calls
 * later is a drop-in change, not a rewrite - see mock.ts's header comment. */

export type SystemLinkState = 'online' | 'degraded' | 'offline'

export interface SystemStatus {
  state: SystemLinkState
  cpuPercent: number
  ramPercent: number
  ramUsedGb: number
  ramTotalGb: number
  storagePercent: number
  storageUsedGb: number
  storageTotalGb: number
  networkDownMbps: number
  networkUpMbps: number
  uptimeHours: number
  agentsOnline: number
  agentsTotal: number
}

export type AgentStatus = 'online' | 'working' | 'waiting' | 'offline'

export interface AgentSummary {
  id: string
  slug: string
  name: string
  role: string
  status: AgentStatus
  currentTask: string | null
  lastActivity: string
  tasksCompletedToday: number
  color: string
}

export type TaskState = 'active' | 'queued' | 'done'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface TaskItem {
  id: string
  title: string
  state: TaskState
  priority: TaskPriority
  progress: number
  agent: string
  dueDate: string | null
}

export type ProjectState = 'active' | 'paused' | 'done' | 'at_risk'

export interface ProjectItem {
  id: string
  name: string
  state: ProjectState
  percentComplete: number
  lastChange: string
  responsibleAgent: string
  color: string
}

export interface ShopifyOrder {
  id: string
  customer: string
  total: number
  status: 'neu' | 'versendet' | 'geliefert' | 'storniert'
  createdAt: string
}

export interface ShopifyBestseller {
  name: string
  unitsSold: number
  revenue: number
}

export interface ShopifyStats {
  ordersToday: number
  revenueToday: number
  revenueMonth: number
  revenueTrend: { date: string; value: number }[]
  visitorsToday: number
  conversionRatePercent: number
  bestsellers: ShopifyBestseller[]
  recentOrders: ShopifyOrder[]
}

export interface GastroOrder {
  id: string
  customer: string
  items: number
  total: number
  deliveryStatus: 'in_kueche' | 'unterwegs' | 'geliefert' | 'storniert'
  createdAt: string
}

export interface SocialStat {
  platform: 'Instagram' | 'Facebook' | 'TikTok'
  followers: number
  engagementPercent: number
  changePercent: number
}

export interface GastroStats {
  ordersToday: number
  revenueToday: number
  avgDeliveryMinutes: number
  googleRating: number
  googleReviewCount: number
  recentOrders: GastroOrder[]
  socialStats: SocialStat[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  attachmentLabel?: string
  createdAt: string
}

export type WorkflowStatus = 'running' | 'success' | 'failed' | 'scheduled'

export interface AutomationWorkflow {
  id: string
  name: string
  status: WorkflowStatus
  trigger: string
  lastRun: string | null
  nextRun: string | null
  successCount7d: number
  failCount7d: number
}

export type LogLevel = 'info' | 'warn' | 'error'

export interface LogEntry {
  id: string
  level: LogLevel
  service: string
  message: string
  timestamp: string
}

export interface ApiStatusEntry {
  name: string
  status: 'ok' | 'degraded' | 'down'
  latencyMs: number
}

export type NotificationType = 'task' | 'error' | 'sale' | 'agent'

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: string
  read: boolean
}

export interface AnalyticsSeriesPoint {
  date: string
  value: number
}

export interface AgentUtilizationPoint {
  agent: string
  utilizationPercent: number
}

export interface TaskStatEntry {
  label: string
  value: number
}

export interface SettingsUserEntry {
  id: string
  name: string
  email: string
  role: 'admin' | 'member'
  active: boolean
}

export interface ApiKeyEntry {
  id: string
  label: string
  provider: string
  maskedKey: string
  createdAt: string
  status: 'aktiv' | 'abgelaufen'
}

export interface BackupEntry {
  id: string
  createdAt: string
  sizeMb: number
  status: 'erfolgreich' | 'fehlgeschlagen'
}
