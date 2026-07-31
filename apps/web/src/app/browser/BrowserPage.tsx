import { useEffect, useRef, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/auth-store'
import type { BrowserServerEnvelope } from '@/types/live'

export function BrowserPage() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [screenshot, setScreenshot] = useState<string | null>(null)
  const [url, setUrl] = useState('')
  const [selector, setSelector] = useState('')
  const [value, setValue] = useState('')
  const [status, setStatus] = useState('Keine Sitzung.')
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    return () => {
      socketRef.current?.close()
      if (sessionId) api.delete(`/browser/sessions/${sessionId}`).catch(() => undefined)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function startSession() {
    if (!accessToken) return
    setStatus('Starte Browser-Session...')
    const session = await api.post<{ id: string }>('/browser/sessions')
    setSessionId(session.id)

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(
      `${protocol}//${window.location.host}/ws/browser/${session.id}?token=${encodeURIComponent(accessToken)}`,
    )
    socket.onmessage = (event) => {
      const envelope: BrowserServerEnvelope = JSON.parse(event.data)
      if (envelope.type === 'screenshot') setScreenshot(envelope.payload.image_base64)
      else if (envelope.type === 'result') setStatus(envelope.payload.message)
      else if (envelope.type === 'error') setStatus(`Fehler: ${envelope.payload.message}`)
    }
    socket.onopen = () => setStatus('Verbunden.')
    socketRef.current = socket
  }

  async function endSession() {
    socketRef.current?.close()
    socketRef.current = null
    if (sessionId) {
      await api.delete(`/browser/sessions/${sessionId}`)
      setSessionId(null)
      setScreenshot(null)
      setStatus('Sitzung beendet.')
    }
  }

  function sendAction(action: string, args: Record<string, string>) {
    socketRef.current?.send(JSON.stringify({ type: 'action', action, args }))
  }

  return (
    <>
      <PageHeader title="Browser" subtitle="Live-Browsersteuerung (Playwright)" />

      {!sessionId ? (
        <Button onClick={startSession}>Browser-Session starten</Button>
      ) : (
        <div className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="URL, z.B. example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendAction('navigate', { url })}
            />
            <Button onClick={() => sendAction('navigate', { url })}>Los</Button>
            <Button variant="ghost" onClick={() => sendAction('go_back', {})}>
              Zurueck
            </Button>
            <Button variant="danger" onClick={endSession}>
              Beenden
            </Button>
          </div>

          <div className="flex gap-2">
            <Input placeholder="CSS-Selektor" value={selector} onChange={(e) => setSelector(e.target.value)} />
            <Input placeholder="Wert (fuer Ausfuellen)" value={value} onChange={(e) => setValue(e.target.value)} />
            <Button variant="ghost" onClick={() => sendAction('fill', { selector, value })}>
              Ausfuellen
            </Button>
            <Button variant="ghost" onClick={() => sendAction('click', { selector })}>
              Klicken
            </Button>
          </div>

          <p className="font-mono text-xs text-text-low">{status}</p>

          <div className="overflow-hidden rounded-lg border border-border bg-panel">
            {screenshot ? (
              <img src={`data:image/png;base64,${screenshot}`} alt="Browser-Vorschau" className="w-full" />
            ) : (
              <div className="flex h-96 items-center justify-center text-text-low">Lade...</div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
