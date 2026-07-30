import { NavLink } from 'react-router-dom'
import { clsx } from '@/lib/clsx'
import { useAuthStore } from '@/store/auth-store'

const NAV_GROUPS: Array<{ label: string; items: Array<{ to: string; label: string }> }> = [
  {
    label: 'Uebersicht',
    items: [
      { to: '/', label: 'Dashboard' },
      { to: '/chat', label: 'Chat' },
      { to: '/agents', label: 'Agenten' },
    ],
  },
  {
    label: 'Arbeit',
    items: [
      { to: '/projects', label: 'Projekte' },
      { to: '/tasks', label: 'Aufgaben' },
      { to: '/files', label: 'Dateien' },
      { to: '/knowledge', label: 'Wissensdatenbank' },
    ],
  },
  {
    label: 'Steuerung',
    items: [
      { to: '/automations', label: 'Automationen' },
      { to: '/browser', label: 'Browser' },
      { to: '/terminal', label: 'Terminal' },
    ],
  },
  {
    label: 'System',
    items: [{ to: '/settings', label: 'Einstellungen' }],
  },
]

export function Sidebar() {
  const { user, logout } = useAuthStore()

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-border-soft bg-bg px-3 py-5">
      <div className="mb-6 px-2">
        <div className="font-mono text-sm font-semibold tracking-tight text-text-hi">
          FUTURIST<span className="text-accent">·</span>OS
        </div>
        <div className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-text-low">
          Phase 0
        </div>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <div className="mb-1 px-2 font-mono text-[10px] uppercase tracking-wider text-text-low">
              {group.label}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    clsx(
                      'block rounded-md border-l-2 border-transparent px-2.5 py-1.5 text-sm transition-colors',
                      isActive
                        ? 'border-accent bg-accent-soft text-accent'
                        : 'text-text-mid hover:bg-panel-2 hover:text-text-hi',
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="mt-4 border-t border-border-soft pt-3 px-2">
        <div className="text-sm text-text-hi">{user?.full_name}</div>
        <div className="mb-2 font-mono text-[11px] text-text-low">{user?.role}</div>
        <button
          onClick={() => logout()}
          className="text-xs text-text-mid hover:text-danger transition-colors"
        >
          Abmelden
        </button>
      </div>
    </aside>
  )
}
