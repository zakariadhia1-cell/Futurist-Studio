import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { useEffect, useRef, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/auth-store'
import type { TerminalServerEnvelope } from '@/types/live'

export function TerminalPage() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const termRef = useRef<Terminal | null>(null)
  const socketRef = useRef<WebSocket | null>(null)

  // Runs once the session exists *and* its container div has actually mounted -
  // starting the terminal from inside the button's click handler doesn't work because
  // that div only renders once sessionId is set, so containerRef.current is still null
  // at the moment the session is created.
  useEffect(() => {
    if (!sessionId || !accessToken || !containerRef.current) return

    const term = new Terminal({
      theme: { background: '#15171b', foreground: '#e8eaed' },
      fontFamily: 'ui-monospace, SF Mono, Cascadia Code, Consolas, monospace',
      fontSize: 13,
      cursorBlink: true,
    })
    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(containerRef.current)
    fitAddon.fit()
    termRef.current = term

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(
      `${protocol}//${window.location.host}/ws/terminal/${sessionId}?token=${encodeURIComponent(accessToken)}`,
    )
    socket.onmessage = (event) => {
      const envelope: TerminalServerEnvelope = JSON.parse(event.data)
      if (envelope.type === 'output') term.write(envelope.data)
      else if (envelope.type === 'closed') term.write('\r\n[Sitzung beendet]\r\n')
    }
    socket.onopen = () => {
      socket.send(JSON.stringify({ type: 'resize', rows: term.rows, cols: term.cols }))
    }
    term.onData((data) => {
      socket.send(JSON.stringify({ type: 'input', data }))
    })
    socketRef.current = socket

    return () => {
      socket.close()
      term.dispose()
    }
  }, [sessionId, accessToken])

  useEffect(() => {
    return () => {
      if (sessionId) api.delete(`/terminal/sessions/${sessionId}`).catch(() => undefined)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function startSession() {
    const session = await api.post<{ id: string }>('/terminal/sessions')
    setSessionId(session.id)
  }

  async function endSession() {
    socketRef.current?.close()
    socketRef.current = null
    termRef.current?.dispose()
    termRef.current = null
    if (sessionId) {
      const id = sessionId
      setSessionId(null)
      await api.delete(`/terminal/sessions/${id}`)
    }
  }

  return (
    <>
      <PageHeader title="Terminal" subtitle="Sandboxed Shell in deinem persoenlichen Workspace" />

      {!sessionId ? (
        <Button onClick={startSession}>Terminal-Session starten</Button>
      ) : (
        <div className="space-y-3">
          <Button variant="danger" onClick={endSession}>
            Beenden
          </Button>
          <div ref={containerRef} className="rounded-lg border border-border bg-panel p-2" />
        </div>
      )}
    </>
  )
}
