import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { api } from '@/lib/api'
import type { GoogleStatus } from '@/types/google'

export function GoogleAccountPanel() {
  const [status, setStatus] = useState<GoogleStatus | null>(null)
  const [connecting, setConnecting] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const callbackResult = searchParams.get('google')

  async function load() {
    setStatus(await api.get<GoogleStatus>('/auth/google/status'))
  }

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    if (!callbackResult) return
    // Drop the query param once shown, so a page refresh doesn't repeat the message.
    load().finally(() => {
      searchParams.delete('google')
      setSearchParams(searchParams, { replace: true })
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callbackResult])

  async function handleConnect() {
    setConnecting(true)
    try {
      const { authorize_url } = await api.get<{ authorize_url: string }>('/auth/google/connect')
      window.location.href = authorize_url
    } finally {
      setConnecting(false)
    }
  }

  async function handleDisconnect() {
    await api.delete('/auth/google')
    await load()
  }

  return (
    <Card className="mt-4 max-w-lg">
      <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">Google-Konto</div>
      <p className="mt-2 text-sm text-text-mid">
        Verbindet Kalender und Gmail mit dem Executive Agent (Termine lesen/anlegen, E-Mails lesen/senden).
      </p>

      {callbackResult === 'connected' && (
        <p className="mt-2 text-sm text-ok">Google-Konto erfolgreich verbunden.</p>
      )}
      {callbackResult === 'error' && (
        <p className="mt-2 text-sm text-danger">Verbindung fehlgeschlagen. Bitte erneut versuchen.</p>
      )}

      {!status ? (
        <p className="mt-3 text-sm text-text-low">lade...</p>
      ) : !status.configured ? (
        <p className="mt-3 text-sm text-text-low">
          Nicht konfiguriert (GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET fehlen serverseitig).
        </p>
      ) : status.connected ? (
        <div className="mt-3 flex items-center justify-between">
          <span className="text-sm text-text-hi">Verbunden als {status.google_email}</span>
          <Button variant="ghost" onClick={handleDisconnect}>
            Trennen
          </Button>
        </div>
      ) : (
        <Button className="mt-3" onClick={handleConnect} disabled={connecting}>
          {connecting ? 'Verbinde...' : 'Mit Google verbinden'}
        </Button>
      )}
    </Card>
  )
}
