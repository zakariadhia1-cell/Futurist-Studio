import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'

export function AppShell() {
  const { pathname } = useLocation()

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        {/* Keyed by path so the fade-in replays on every navigation, not just first mount. */}
        <div key={pathname} className="page-enter">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
