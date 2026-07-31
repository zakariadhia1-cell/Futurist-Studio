import { useState } from 'react'
import { Bell, Bot, CircleAlert, ListChecks, ShoppingBag } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { getNotifications } from '../data/mock'
import { useMock } from '../data/useMock'
import type { NotificationItem, NotificationType } from '../data/types'
import { clsx } from '@/lib/clsx'

const TYPE_META: Record<NotificationType, { icon: typeof Bell; color: string }> = {
  task: { icon: ListChecks, color: 'var(--color-neon-blue)' },
  error: { icon: CircleAlert, color: 'var(--color-neon-red)' },
  sale: { icon: ShoppingBag, color: 'var(--color-ok)' },
  agent: { icon: Bot, color: 'var(--color-neon-violet)' },
}

export function NotificationsPage() {
  const { data, loading } = useMock(getNotifications)
  const [readIds, setReadIds] = useState<Set<string>>(new Set())

  const items: NotificationItem[] = (data ?? []).map((n) => (readIds.has(n.id) ? { ...n, read: true } : n))
  const unread = items.filter((n) => !n.read)

  return (
    <>
      <SectionHeader
        icon={Bell}
        title="Benachrichtigungen"
        subtitle="Neue Aufgaben, Fehler, Verkaeufe und Agentenmeldungen an einem Ort"
        action={
          unread.length > 0 && (
            <button
              onClick={() => setReadIds(new Set(items.map((n) => n.id)))}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-white/50 transition-colors hover:bg-white/[0.06] hover:text-white"
            >
              Alle als gelesen markieren
            </button>
          )
        }
      />

      {loading ? (
        <LoadingState />
      ) : (
        <div className="space-y-2.5">
          {items.map((item) => {
            const meta = TYPE_META[item.type]
            const Icon = meta.icon
            return (
              <GlassCard
                key={item.id}
                onClick={() => setReadIds((prev) => new Set(prev).add(item.id))}
                className={clsx('flex cursor-pointer items-start gap-3.5 transition-opacity', item.read && 'opacity-50')}
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg" style={{ background: `${meta.color}18` }}>
                  <Icon className="h-4 w-4" style={{ color: meta.color }} strokeWidth={1.75} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">{item.title}</span>
                    {!item.read && <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--color-neon-blue)]" />}
                  </div>
                  <p className="mt-0.5 text-sm text-white/50">{item.message}</p>
                </div>
                <span className="shrink-0 whitespace-nowrap text-xs text-white/30">{item.timestamp}</span>
              </GlassCard>
            )
          })}
        </div>
      )}
    </>
  )
}
