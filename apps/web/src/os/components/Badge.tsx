import type { ReactNode } from 'react'
import { clsx } from '@/lib/clsx'

export type BadgeTone = 'neutral' | 'ok' | 'warn' | 'danger' | 'info' | 'violet'

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: 'bg-white/[0.06] text-white/60 border-white/10',
  ok: 'bg-[color:var(--color-ok)]/10 text-[color:var(--color-ok)] border-[color:var(--color-ok)]/25',
  warn: 'bg-[color:var(--color-neon-amber)]/10 text-[color:var(--color-neon-amber)] border-[color:var(--color-neon-amber)]/25',
  danger: 'bg-[color:var(--color-neon-red)]/10 text-[color:var(--color-neon-red)] border-[color:var(--color-neon-red)]/25',
  info: 'bg-[color:var(--color-neon-blue)]/10 text-[color:var(--color-neon-blue)] border-[color:var(--color-neon-blue)]/25',
  violet: 'bg-[color:var(--color-neon-violet)]/10 text-[color:var(--color-neon-violet)] border-[color:var(--color-neon-violet)]/25',
}

export function Badge({
  tone = 'neutral',
  dot = false,
  className,
  children,
}: {
  tone?: BadgeTone
  dot?: boolean
  className?: string
  children: ReactNode
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wider',
        TONE_CLASSES[tone],
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}
