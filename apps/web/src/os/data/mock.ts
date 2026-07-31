/**
 * Dummy data for the OS control center, shaped exactly like the API responses that will
 * eventually replace it (see the explicit request: "Alle Daten sollen ueber APIs
 * vorbereitet werden, sodass spaeter echte Daten angeschlossen werden koennen").
 *
 * Wiring a real backend later means writing one `app/api/v1/os/<section>.py` FastAPI
 * router per section returning these same shapes (types.ts) and swapping the
 * `get<Section>()` call below for `api.get<T>('/os/<section>')` - the page components
 * never need to change.
 *
 * Shopify and "Gastro Prinz" have no backend integration in this codebase at all yet -
 * those two sections are pure mock until that integration exists.
 */
import type {
  AgentSummary,
  AgentUtilizationPoint,
  AnalyticsSeriesPoint,
  ApiKeyEntry,
  ApiStatusEntry,
  AutomationWorkflow,
  BackupEntry,
  ChatMessage,
  GastroStats,
  LogEntry,
  NotificationItem,
  ProjectItem,
  SettingsUserEntry,
  ShopifyStats,
  SystemStatus,
  TaskItem,
  TaskStatEntry,
} from './types'

function delay<T>(value: T, ms = 220): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export function getSystemStatus(): Promise<SystemStatus> {
  return delay({
    state: 'online',
    cpuPercent: 34,
    ramPercent: 58,
    ramUsedGb: 9.3,
    ramTotalGb: 16,
    storagePercent: 41,
    storageUsedGb: 205,
    storageTotalGb: 500,
    networkDownMbps: 182,
    networkUpMbps: 37,
    uptimeHours: 142,
    agentsOnline: 5,
    agentsTotal: 7,
  })
}

export function getAgents(): Promise<AgentSummary[]> {
  return delay([
    {
      id: 'executive',
      slug: 'executive',
      name: 'Executive Agent',
      role: 'Koordination & Delegation',
      status: 'working',
      currentTask: 'Delegiert Analyse an Research Agent',
      lastActivity: 'vor 12 Sek.',
      tasksCompletedToday: 14,
      color: 'var(--color-neon-blue)',
    },
    {
      id: 'developer',
      slug: 'developer',
      name: 'Developer Agent',
      role: 'Code & Terminal',
      status: 'working',
      currentTask: 'Refactoring app/os/ Module',
      lastActivity: 'vor 3 Sek.',
      tasksCompletedToday: 9,
      color: 'var(--color-neon-cyan)',
    },
    {
      id: 'research',
      slug: 'research',
      name: 'Research Agent',
      role: 'Web & Wissensdatenbank',
      status: 'online',
      currentTask: null,
      lastActivity: 'vor 1 Min.',
      tasksCompletedToday: 6,
      color: 'var(--color-neon-violet)',
    },
    {
      id: 'design',
      slug: 'design',
      name: 'Design Agent',
      role: 'Bildgenerierung',
      status: 'waiting',
      currentTask: 'Wartet auf Freigabe (Logo-Entwurf)',
      lastActivity: 'vor 6 Min.',
      tasksCompletedToday: 3,
      color: 'var(--color-neon-amber)',
    },
    {
      id: 'marketing',
      slug: 'marketing',
      name: 'Marketing Agent',
      role: 'SEO & Copy',
      status: 'online',
      currentTask: null,
      lastActivity: 'vor 18 Min.',
      tasksCompletedToday: 4,
      color: 'var(--color-neon-blue)',
    },
    {
      id: 'finance',
      slug: 'finance',
      name: 'Finance Agent',
      role: 'Kalkulation & Rechnungen',
      status: 'offline',
      currentTask: null,
      lastActivity: 'vor 3 Std.',
      tasksCompletedToday: 2,
      color: 'var(--color-neon-cyan)',
    },
    {
      id: 'automation',
      slug: 'automation',
      name: 'Automation Agent',
      role: 'n8n & Workflows',
      status: 'working',
      currentTask: 'Ueberwacht 3 laufende Workflows',
      lastActivity: 'vor 24 Sek.',
      tasksCompletedToday: 21,
      color: 'var(--color-neon-violet)',
    },
  ])
}

export function getTasks(): Promise<TaskItem[]> {
  return delay([
    { id: 't1', title: 'Q3-Report zusammenfassen', state: 'active', priority: 'high', progress: 72, agent: 'Research Agent', dueDate: 'heute, 18:00' },
    { id: 't2', title: 'Landingpage-Copy ueberarbeiten', state: 'active', priority: 'medium', progress: 45, agent: 'Marketing Agent', dueDate: 'morgen' },
    { id: 't3', title: 'API-Dokumentation aktualisieren', state: 'active', priority: 'medium', progress: 30, agent: 'Developer Agent', dueDate: 'morgen' },
    { id: 't4', title: 'Logo-Varianten generieren', state: 'queued', priority: 'low', progress: 0, agent: 'Design Agent', dueDate: null },
    { id: 't5', title: 'Rechnung #2044 pruefen', state: 'queued', priority: 'medium', progress: 0, agent: 'Finance Agent', dueDate: 'in 2 Tagen' },
    { id: 't6', title: 'n8n-Workflow "Lead-Sync" testen', state: 'queued', priority: 'high', progress: 0, agent: 'Automation Agent', dueDate: 'heute' },
    { id: 't7', title: 'Onboarding-E-Mail-Sequenz', state: 'done', priority: 'medium', progress: 100, agent: 'Marketing Agent', dueDate: null },
    { id: 't8', title: 'Security-Audit P0-Fixes', state: 'done', priority: 'high', progress: 100, agent: 'Developer Agent', dueDate: null },
    { id: 't9', title: 'Wettbewerbsanalyse Q2', state: 'done', priority: 'low', progress: 100, agent: 'Research Agent', dueDate: null },
  ])
}

export function getProjects(): Promise<ProjectItem[]> {
  return delay([
    { id: 'p1', name: 'FUTURIST OS Launch', state: 'active', percentComplete: 78, lastChange: 'vor 5 Min.', responsibleAgent: 'Executive Agent', color: 'var(--color-neon-blue)' },
    { id: 'p2', name: 'Shopify Relaunch', state: 'active', percentComplete: 52, lastChange: 'vor 1 Std.', responsibleAgent: 'Marketing Agent', color: 'var(--color-neon-cyan)' },
    { id: 'p3', name: 'Gastro Prinz Onlinebestellung', state: 'at_risk', percentComplete: 34, lastChange: 'vor 3 Std.', responsibleAgent: 'Developer Agent', color: 'var(--color-neon-red)' },
    { id: 'p4', name: 'Content-Kalender Q4', state: 'paused', percentComplete: 20, lastChange: 'gestern', responsibleAgent: 'Marketing Agent', color: 'var(--color-neon-amber)' },
    { id: 'p5', name: 'Interne Wissensdatenbank', state: 'done', percentComplete: 100, lastChange: 'vor 4 Tagen', responsibleAgent: 'Research Agent', color: 'var(--color-neon-violet)' },
  ])
}

export function getShopifyStats(): Promise<ShopifyStats> {
  return delay({
    ordersToday: 47,
    revenueToday: 3218.5,
    revenueMonth: 58420.9,
    revenueTrend: [
      { date: 'Mo', value: 4200 },
      { date: 'Di', value: 3800 },
      { date: 'Mi', value: 5100 },
      { date: 'Do', value: 4600 },
      { date: 'Fr', value: 6200 },
      { date: 'Sa', value: 7100 },
      { date: 'So', value: 3218.5 },
    ],
    visitorsToday: 1842,
    conversionRatePercent: 2.55,
    bestsellers: [
      { name: 'FUTURIST Tee Classic', unitsSold: 128, revenue: 2560 },
      { name: 'Neon Hoodie', unitsSold: 64, revenue: 3840 },
      { name: 'Sticker Pack v2', unitsSold: 211, revenue: 1055 },
    ],
    recentOrders: [
      { id: '#10482', customer: 'L. Weber', total: 89.9, status: 'neu', createdAt: 'vor 4 Min.' },
      { id: '#10481', customer: 'S. Klein', total: 34.5, status: 'versendet', createdAt: 'vor 22 Min.' },
      { id: '#10480', customer: 'M. Roth', total: 129.0, status: 'geliefert', createdAt: 'vor 1 Std.' },
      { id: '#10479', customer: 'J. Fischer', total: 19.9, status: 'storniert', createdAt: 'vor 2 Std.' },
    ],
  })
}

export function getGastroStats(): Promise<GastroStats> {
  return delay({
    ordersToday: 63,
    revenueToday: 1487.3,
    avgDeliveryMinutes: 28,
    googleRating: 4.6,
    googleReviewCount: 312,
    recentOrders: [
      { id: 'G-2291', customer: 'Tisch 4', items: 3, total: 42.5, deliveryStatus: 'in_kueche', createdAt: 'vor 2 Min.' },
      { id: 'G-2290', customer: 'Lieferung Nord', items: 2, total: 27.9, deliveryStatus: 'unterwegs', createdAt: 'vor 14 Min.' },
      { id: 'G-2289', customer: 'Abholung', items: 1, total: 12.5, deliveryStatus: 'geliefert', createdAt: 'vor 25 Min.' },
      { id: 'G-2288', customer: 'Lieferung Sued', items: 4, total: 58.0, deliveryStatus: 'geliefert', createdAt: 'vor 40 Min.' },
    ],
    socialStats: [
      { platform: 'Instagram', followers: 4820, engagementPercent: 6.1, changePercent: 3.4 },
      { platform: 'Facebook', followers: 2103, engagementPercent: 2.8, changePercent: -0.6 },
      { platform: 'TikTok', followers: 9750, engagementPercent: 11.4, changePercent: 12.1 },
    ],
  })
}

export function getChatHistory(): Promise<ChatMessage[]> {
  return delay([
    { id: 'c1', role: 'user', content: 'Fass mir den Q3-Report zusammen.', createdAt: '09:14' },
    {
      id: 'c2',
      role: 'assistant',
      content: 'Umsatz +18% ggue. Q2, groesster Treiber ist Shopify (Neon Hoodie). Ich habe Research Agent fuer die Details delegiert.',
      createdAt: '09:14',
    },
    { id: 'c3', role: 'user', content: 'Analysiere bitte diesen Screenshot.', attachmentLabel: 'dashboard-fehler.png', createdAt: '09:20' },
    {
      id: 'c4',
      role: 'assistant',
      content: 'Der Fehler kommt aus terminal_manager.py Zeile 42 - env wird nicht korrekt gesetzt. Soll ich einen Fix vorschlagen?',
      createdAt: '09:20',
    },
  ])
}

export function getAutomations(): Promise<AutomationWorkflow[]> {
  return delay([
    { id: 'w1', name: 'Lead-Sync (CRM -> Shopify)', status: 'running', trigger: 'Alle 15 Min.', lastRun: 'vor 3 Min.', nextRun: 'in 12 Min.', successCount7d: 612, failCount7d: 2 },
    { id: 'w2', name: 'Google Reviews -> Slack', status: 'success', trigger: 'Webhook', lastRun: 'vor 40 Min.', nextRun: null, successCount7d: 88, failCount7d: 0 },
    { id: 'w3', name: 'Taegliches Umsatz-Reporting', status: 'scheduled', trigger: 'Taeglich 07:00', lastRun: 'heute, 07:00', nextRun: 'morgen, 07:00', successCount7d: 7, failCount7d: 0 },
    { id: 'w4', name: 'Rechnungs-Mahnlauf', status: 'failed', trigger: 'Woechentlich Mo', lastRun: 'vor 2 Std.', nextRun: 'naechste Woche', successCount7d: 3, failCount7d: 1 },
  ])
}

export function getLogs(): Promise<LogEntry[]> {
  return delay([
    { id: 'l1', level: 'info', service: 'api', message: 'Health-Check ok (12ms)', timestamp: 'vor 8 Sek.' },
    { id: 'l2', level: 'info', service: 'automation-agent', message: 'Workflow "Lead-Sync" erfolgreich', timestamp: 'vor 3 Min.' },
    { id: 'l3', level: 'warn', service: 'terminal', message: 'Rate-Limit fuer terminal_session bei 80% (16/20)', timestamp: 'vor 9 Min.' },
    { id: 'l4', level: 'error', service: 'mcp-client', message: 'Verbindung zu MCP-Server "invoice-tool" fehlgeschlagen (Timeout)', timestamp: 'vor 22 Min.' },
    { id: 'l5', level: 'info', service: 'browser-worker', message: 'Session geschlossen (Idle > 10 Min.)', timestamp: 'vor 31 Min.' },
    { id: 'l6', level: 'warn', service: 'knowledge', message: 'Embedding-Job dauerte 4.2s (> 3s Schwelle)', timestamp: 'vor 1 Std.' },
  ])
}

export function getApiStatus(): Promise<ApiStatusEntry[]> {
  return delay([
    { name: 'FUTURIST API', status: 'ok', latencyMs: 41 },
    { name: 'PostgreSQL', status: 'ok', latencyMs: 6 },
    { name: 'Redis', status: 'ok', latencyMs: 2 },
    { name: 'Anthropic API', status: 'ok', latencyMs: 612 },
    { name: 'OpenAI API', status: 'degraded', latencyMs: 1840 },
    { name: 'n8n', status: 'ok', latencyMs: 88 },
    { name: 'Shopify Admin API', status: 'ok', latencyMs: 210 },
  ])
}

export function getNotifications(): Promise<NotificationItem[]> {
  return delay([
    { id: 'n1', type: 'sale', title: 'Neue Bestellung', message: 'Shopify #10482 ueber 89,90 EUR', timestamp: 'vor 4 Min.', read: false },
    { id: 'n2', type: 'agent', title: 'Design Agent wartet', message: 'Freigabe fuer Logo-Entwurf benoetigt', timestamp: 'vor 6 Min.', read: false },
    { id: 'n3', type: 'error', title: 'MCP-Verbindung fehlgeschlagen', message: 'invoice-tool antwortet nicht (Timeout)', timestamp: 'vor 22 Min.', read: false },
    { id: 'n4', type: 'task', title: 'Aufgabe erledigt', message: 'Security-Audit P0-Fixes abgeschlossen', timestamp: 'vor 1 Std.', read: true },
    { id: 'n5', type: 'sale', title: 'Tagesziel erreicht', message: 'Gastro Prinz: 60+ Bestellungen heute', timestamp: 'vor 2 Std.', read: true },
  ])
}

export function getRevenueSeries(): Promise<AnalyticsSeriesPoint[]> {
  return delay([
    { date: '01.07', value: 3200 },
    { date: '08.07', value: 4100 },
    { date: '15.07', value: 3900 },
    { date: '22.07', value: 5200 },
    { date: '29.07', value: 4700 },
    { date: '31.07', value: 4700 },
  ])
}

export function getAgentUtilization(): Promise<AgentUtilizationPoint[]> {
  return delay([
    { agent: 'Executive', utilizationPercent: 82 },
    { agent: 'Developer', utilizationPercent: 91 },
    { agent: 'Research', utilizationPercent: 54 },
    { agent: 'Design', utilizationPercent: 38 },
    { agent: 'Marketing', utilizationPercent: 47 },
    { agent: 'Finance', utilizationPercent: 21 },
    { agent: 'Automation', utilizationPercent: 76 },
  ])
}

export function getTaskStats(): Promise<TaskStatEntry[]> {
  return delay([
    { label: 'Erledigt', value: 3 },
    { label: 'Aktiv', value: 3 },
    { label: 'Warteschlange', value: 3 },
  ])
}

export function getPerformanceSeries(): Promise<AnalyticsSeriesPoint[]> {
  return delay([
    { date: '00:00', value: 120 },
    { date: '04:00', value: 98 },
    { date: '08:00', value: 210 },
    { date: '12:00', value: 340 },
    { date: '16:00', value: 290 },
    { date: '20:00', value: 175 },
  ])
}

export function getSettingsUsers(): Promise<SettingsUserEntry[]> {
  return delay([
    { id: 'u1', name: 'Zakaria', email: 'zakariadhia1@gmail.com', role: 'admin', active: true },
    { id: 'u2', name: 'Team-Mitglied', email: 'member@futurist.os', role: 'member', active: true },
  ])
}

export function getApiKeys(): Promise<ApiKeyEntry[]> {
  return delay([
    { id: 'k1', label: 'Anthropic', provider: 'anthropic', maskedKey: 'sk-ant-...8f2a', createdAt: '12.05.2026', status: 'aktiv' },
    { id: 'k2', label: 'OpenAI', provider: 'openai', maskedKey: 'sk-...91cd', createdAt: '02.06.2026', status: 'aktiv' },
    { id: 'k3', label: 'Shopify Admin', provider: 'shopify', maskedKey: 'shpat_...44b1', createdAt: '18.03.2026', status: 'aktiv' },
    { id: 'k4', label: 'ElevenLabs', provider: 'elevenlabs', maskedKey: 'el_...09aa', createdAt: '01.01.2026', status: 'abgelaufen' },
  ])
}

export function getBackups(): Promise<BackupEntry[]> {
  return delay([
    { id: 'b1', createdAt: 'heute, 03:00', sizeMb: 842, status: 'erfolgreich' },
    { id: 'b2', createdAt: 'gestern, 03:00', sizeMb: 838, status: 'erfolgreich' },
    { id: 'b3', createdAt: 'vor 2 Tagen, 03:00', sizeMb: 831, status: 'erfolgreich' },
    { id: 'b4', createdAt: 'vor 3 Tagen, 03:00', sizeMb: 0, status: 'fehlgeschlagen' },
  ])
}
