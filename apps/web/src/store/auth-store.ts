import { create } from 'zustand'
import type { TokenPair, User } from '@/types/auth'

const API_BASE = '/api/v1'
const REFRESH_TOKEN_KEY = 'futurist_refresh_token'

// Refresh tokens are single-use (rotated on every call). Concurrent callers - e.g. React
// StrictMode's double effect-invocation, or multiple tabs - must share one in-flight
// request instead of each rotating the token and invalidating the other's copy.
let inFlightRefresh: Promise<boolean> | null = null

interface AuthState {
  accessToken: string | null
  user: User | null
  status: 'idle' | 'loading' | 'authenticated' | 'unauthenticated'
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<boolean>
  hydrate: () => Promise<void>
}

async function fetchMe(accessToken: string): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!res.ok) throw new Error('Sitzung ungueltig')
  return res.json()
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  user: null,
  status: 'idle',
  error: null,

  login: async (email, password) => {
    set({ status: 'loading', error: null })
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: 'Anmeldung fehlgeschlagen' }))
      set({ status: 'unauthenticated', error: body.detail })
      throw new Error(body.detail)
    }
    const tokens: TokenPair = await res.json()
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
    const user = await fetchMe(tokens.access_token)
    set({ accessToken: tokens.access_token, user, status: 'authenticated', error: null })
  },

  register: async (email, password, fullName) => {
    set({ status: 'loading', error: null })
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: 'Registrierung fehlgeschlagen' }))
      set({ status: 'unauthenticated', error: body.detail })
      throw new Error(body.detail)
    }
    await get().login(email, password)
  },

  logout: async () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    set({ accessToken: null, user: null, status: 'unauthenticated' })
    if (refreshToken) {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(() => undefined)
    }
  },

  refresh: async () => {
    if (inFlightRefresh) return inFlightRefresh

    const run = async () => {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (!refreshToken) {
        set({ status: 'unauthenticated' })
        return false
      }
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!res.ok) {
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        set({ accessToken: null, user: null, status: 'unauthenticated' })
        return false
      }
      const tokens: TokenPair = await res.json()
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
      set({ accessToken: tokens.access_token })
      return true
    }

    inFlightRefresh = run().finally(() => {
      inFlightRefresh = null
    })
    return inFlightRefresh
  },

  hydrate: async () => {
    const ok = await get().refresh()
    if (!ok) return
    const { accessToken } = get()
    if (!accessToken) return
    try {
      const user = await fetchMe(accessToken)
      set({ user, status: 'authenticated' })
    } catch {
      set({ status: 'unauthenticated' })
    }
  },
}))
