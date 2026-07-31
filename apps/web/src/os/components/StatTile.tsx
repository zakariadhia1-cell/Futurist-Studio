import type { LucideIcon } from 'lucide-react'
import { GlassCard } from './GlassCard'
import { clsx } from '@/lib/clsx'

interface StatTileProps {
  label: string
  value: string
  icon: LucideIcon
  trend?: { value: string; positive: boolean }
  accent?: 'blue' | 'cyan' | 'violet' | 'amber' | 'red'
}

const ACCENT_TEXT: Record<NonNullable<StatTileProps['accent']>, string> = {
  blue: 'text-[color:var(--color-neon-blue)]',
  cyan: 'text-[color:var(--color-neon-cyan)]',
  violet: 'text-[color:var(--color-neon-violet)]',
  amber: 'text-[color:var(--color-neon-amber)]',
  red: 'text-[color:var(--color-neon-red)]',
}

const ACCENT_BG: Record<NonNullable<StatTileProps['accent']>, string> = {
  blue: 'bg-[color:var(--color-neon-blue)]/10',
  cyan: 'bg-[color:var(--color-neon-cyan)]/10',
  violet: 'bg-[color:var(--color-neon-violet)]/10',
  amber: 'bg-[color:var(--color-neon-amber)]/10',
  red: 'bg-[color:var(--color-neon-red)]/10',
}

export function StatTile({ label, value, icon: Icon, trend, accent = 'blue' }: StatTileProps) {
  return (
    <GlassCard className="flex items-center gap-4">
      <div className={clsx('flex h-11 w-11 shrink-0 items-center justify-center rounded-xl', ACCENT_BG[accent])}>
        <Icon className={clsx('h-5 w-5', ACCENT_TEXT[accent])} strokeWidth={1.75} />
      </div>
      <div className="min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-wider text-white/45">{label}</div>
        <div className="mt-0.5 flex items-baseline gap-2">
          <span className="truncate text-lg font-semibold text-white">{value}</span>
          {trend && (
            <span className={clsx('text-xs font-medium', trend.positive ? 'text-[color:var(--color-ok)]' : 'text-[color:var(--color-neon-red)]')}>
              {trend.positive ? '+' : ''}
              {trend.value}
            </span>
          )}
        </div>
      </div>
    </GlassCard>
  )
}
