import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/card'
import { api } from '@/lib/api'
import type { Agent } from '@/types/chat'

export function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])

  useEffect(() => {
    api.get<Agent[]>('/agents').then(setAgents)
  }, [])

  return (
    <>
      <PageHeader title="Agenten" subtitle="Executive Agent koordiniert die Fachagenten" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {agents.map((a) => (
          <Card key={a.id}>
            <div className="text-sm font-medium text-text-hi">{a.name}</div>
            {a.description && <p className="mt-1 text-sm text-text-mid">{a.description}</p>}
            {a.tools.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {a.tools.map((tool) => (
                  <span
                    key={tool}
                    className="rounded bg-panel-2 px-1.5 py-0.5 font-mono text-[10px] text-text-mid"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>
    </>
  )
}
