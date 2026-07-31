import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/auth-store'

export function RequireAuth() {
  const { status, hydrate } = useAuthStore()

  useEffect(() => {
    if (status === 'idle') hydrate()
  }, [status, hydrate])

  if (status === 'idle' || status === 'loading') {
    return <div className="flex min-h-screen items-center justify-center text-text-mid">Lade...</div>
  }
  if (status !== 'authenticated') return <Navigate to="/login" replace />
  return <Outlet />
}
