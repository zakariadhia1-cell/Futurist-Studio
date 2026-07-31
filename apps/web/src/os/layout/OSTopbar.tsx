import { useEffect, useState } from 'react'
import { Bell, LogOut, Menu, Wifi } from 'lucide-react'
import { useAuthStore } from '@/store/auth-store'

const DATE_FORMAT = new Intl.DateTimeFormat('de-DE', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })
const TIME_FORMAT = new Intl.DateTimeFormat('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

export function OSTopbar({ unreadCount = 0, onMenuClick }: { unreadCount?: number; onMenuClick: () => void }) {
  const { user, logout } = useAuthStore()
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const interval = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(interval)
  }, [])

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-white/10 bg-black/20 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex min-w-0 items-center gap-3 sm:gap-4">
        <button
          onClick={onMenuClick}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 text-white/60 transition-colors hover:bg-white/[0.06] hover:text-white lg:hidden"
        >
          <Menu className="h-4 w-4" strokeWidth={1.75} />
        </button>
        <div className="flex shrink-0 items-center gap-1.5 rounded-full border border-[color:var(--color-ok)]/30 bg-[color:var(--color-ok)]/10 px-2.5 py-1">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--color-ok)]" />
          <span className="hidden font-mono text-[10px] uppercase tracking-wider text-[color:var(--color-ok)] sm:inline">
            System online
          </span>
          <span className="font-mono text-[10px] uppercase tracking-wider text-[color:var(--color-ok)] sm:hidden">Online</span>
        </div>
        <div className="hidden items-center gap-1.5 text-white/40 md:flex">
          <Wifi className="h-3.5 w-3.5" strokeWidth={1.75} />
          <span className="font-mono text-[11px]">Stabil</span>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3 sm:gap-5">
        <div className="hidden text-right font-mono leading-tight md:block">
          <div className="text-sm text-white">{TIME_FORMAT.format(now)}</div>
          <div className="text-[10px] uppercase tracking-wider text-white/35">{DATE_FORMAT.format(now)}</div>
        </div>

        <button className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 text-white/60 transition-colors hover:bg-white/[0.06] hover:text-white">
          <Bell className="h-4 w-4" strokeWidth={1.75} />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[color:var(--color-neon-red)] px-1 font-mono text-[9px] font-semibold text-black">
              {unreadCount}
            </span>
          )}
        </button>

        <div className="flex items-center gap-2.5">
          <div className="hidden text-right leading-tight lg:block">
            <div className="text-sm text-white">{user?.full_name}</div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-white/35">{user?.role}</div>
          </div>
          <div className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[color:var(--color-neon-blue)]/30 bg-[color:var(--color-neon-blue)]/10 font-mono text-xs text-[color:var(--color-neon-blue)] sm:flex">
            {(user?.full_name ?? '?').slice(0, 1).toUpperCase()}
          </div>
          <button
            onClick={() => logout()}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 text-white/50 transition-colors hover:border-[color:var(--color-neon-red)]/40 hover:text-[color:var(--color-neon-red)]"
            title="Abmelden"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.75} />
          </button>
        </div>
      </div>
    </header>
  )
}
