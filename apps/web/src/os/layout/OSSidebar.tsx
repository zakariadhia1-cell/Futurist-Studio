import { NavLink } from 'react-router-dom'
import { ArrowLeftToLine, X } from 'lucide-react'
import { clsx } from '@/lib/clsx'
import { OS_NAV } from './nav'

/** Static on lg+ screens (part of the flex row layout); below that it's a fixed
 * off-canvas drawer toggled from OSTopbar's hamburger button - a plain w-64 aside with
 * no responsive handling would push page content off-screen on phone widths instead of
 * collapsing, which is what happened before this. */
export function OSSidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden" onClick={onClose} aria-hidden="true" />
      )}

      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 flex h-full w-64 shrink-0 flex-col border-r border-white/10 bg-[color:var(--color-os-panel)]/95 backdrop-blur-xl transition-transform duration-200 lg:static lg:translate-x-0 lg:bg-black/30',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-center justify-between gap-2.5 px-5 py-6">
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-[color:var(--color-neon-blue)]/40 bg-[color:var(--color-neon-blue)]/10">
              <div className="h-2.5 w-2.5 rounded-full bg-[color:var(--color-neon-blue)] shadow-[0_0_10px_var(--color-neon-blue)]" />
            </div>
            <div>
              <div className="font-mono text-sm font-semibold tracking-wide text-white">
                FUTURIST<span className="text-[color:var(--color-neon-blue)]">·OS</span>
              </div>
              <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-white/35">Kontrollzentrum</div>
            </div>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white lg:hidden">
            <X className="h-4.5 w-4.5" strokeWidth={1.75} />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3">
          {OS_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-150',
                  isActive
                    ? 'bg-[color:var(--color-neon-blue)]/10 text-white shadow-[inset_0_0_0_1px_rgba(53,200,255,0.25)]'
                    : 'text-white/50 hover:bg-white/[0.05] hover:text-white/85',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon
                    className={clsx('h-4 w-4 shrink-0', isActive ? 'text-[color:var(--color-neon-blue)]' : 'text-white/40 group-hover:text-white/70')}
                    strokeWidth={1.75}
                  />
                  <span className="truncate">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 p-3">
          <NavLink
            to="/"
            className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-white/40 transition-colors hover:bg-white/[0.05] hover:text-white/70"
          >
            <ArrowLeftToLine className="h-3.5 w-3.5" strokeWidth={1.75} />
            Zurueck zur Standardansicht
          </NavLink>
        </div>
      </aside>
    </>
  )
}
