import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/card'
import { useAuthStore } from '@/store/auth-store'

interface HealthStatus {
  status: string
  database: boolean
  redis: boolean
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const [health, setHealth] = useState<HealthStatus | null>(null)

  useEffect(() => {
    fetch('/api/v1/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  return (
    <>
      <PageHeader
        title={`Willkommen zurueck, ${user?.full_name ?? ''}`}
        subtitle="FUTURIST OS - Phase 0: Fundament"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">System</div>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${health?.status === 'ok' ? 'bg-ok' : 'bg-warn'}`}
            />
            <span className="text-text-hi">{health ? health.status : 'lade...'}</span>
          </div>
        </Card>
        <Card>
          <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">Datenbank</div>
          <div className="mt-2 text-text-hi">{health?.database ? 'verbunden' : '-'}</div>
        </Card>
        <Card>
          <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">Redis</div>
          <div className="mt-2 text-text-hi">{health?.redis ? 'verbunden' : '-'}</div>
        </Card>
      </div>

      <Card className="mt-4">
        <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">Naechste Phase</div>
        <p className="mt-2 text-sm text-text-mid">
          Phase 1 - Core Chat: Model-Abstraction (OpenAI/Anthropic/Ollama), Executive Agent, Chat-UI mit
          WebSocket-Streaming. Siehe{' '}
          <code className="rounded bg-panel-2 px-1 py-0.5 text-text-hi">
            docs/architecture/FUTURIST_OS_ARCHITECTURE.md
          </code>
          .
        </p>
      </Card>
    </>
  )
}
