import { useAuthStore } from '@/store/auth-store'

const API_BASE = '/api/v1'

class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

async function rawRequest(path: string, options: RequestInit = {}, retry = true): Promise<Response> {
  const { accessToken } = useAuthStore.getState()

  const headers = new Headers(options.headers)
  // FormData sets its own multipart Content-Type (with boundary) - fetch derives it
  // automatically only when we don't set one ourselves.
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (response.status === 401 && retry) {
    const refreshed = await useAuthStore.getState().refresh()
    if (refreshed) return rawRequest(path, options, false)
    useAuthStore.getState().logout()
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(response.status, body.detail ?? 'Unbekannter Fehler')
  }

  return response
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await rawRequest(path, options)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  upload: <T>(path: string, formData: FormData) => request<T>(path, { method: 'POST', body: formData }),
  downloadBlob: async (path: string) => (await rawRequest(path)).blob(),
}

export { ApiError, API_BASE }
