import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

export function SectionHeader({
  title,
  subtitle,
  icon: Icon,
  action,
}: {
  title: string
  subtitle?: string
  icon?: LucideIcon
  action?: ReactNode
}) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[color:var(--color-neon-blue)]/25 bg-[color:var(--color-neon-blue)]/10">
            <Icon className="h-4 w-4 text-[color:var(--color-neon-blue)]" strokeWidth={1.75} />
          </div>
        )}
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-white">{title}</h1>
          {subtitle && <p className="mt-0.5 text-sm text-white/50">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  )
}
