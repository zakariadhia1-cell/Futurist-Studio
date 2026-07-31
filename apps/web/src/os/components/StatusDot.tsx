import { clsx } from '@/lib/clsx'
import type { AgentStatus } from '../data/types'
import { Badge, type BadgeTone } from './Badge'

const AGENT_STATUS_LABEL: Record<AgentStatus, string> = {
  online: 'Online',
  working: 'Arbeitet',
  waiting: 'Wartet',
  offline: 'Offline',
}

const AGENT_STATUS_TONE: Record<AgentStatus, BadgeTone> = {
  online: 'ok',
  working: 'info',
  waiting: 'warn',
  offline: 'neutral',
}

export function AgentStatusBadge({ status }: { status: AgentStatus }) {
  return (
    <Badge tone={AGENT_STATUS_TONE[status]} dot>
      {AGENT_STATUS_LABEL[status]}
    </Badge>
  )
}

export function PulseDot({ tone = 'ok' }: { tone?: 'ok' | 'warn' | 'danger' | 'neutral' }) {
  const color =
    tone === 'ok'
      ? 'bg-[color:var(--color-ok)]'
      : tone === 'warn'
        ? 'bg-[color:var(--color-neon-amber)]'
        : tone === 'danger'
          ? 'bg-[color:var(--color-neon-red)]'
          : 'bg-white/30'
  return (
    <span className="relative flex h-2 w-2">
      <span className={clsx('absolute inline-flex h-full w-full animate-ping rounded-full opacity-60', color)} />
      <span className={clsx('relative inline-flex h-2 w-2 rounded-full', color)} />
    </span>
  )
}
