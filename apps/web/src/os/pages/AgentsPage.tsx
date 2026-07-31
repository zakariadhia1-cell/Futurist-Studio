import { useState } from 'react'
import { Bot, Play, RotateCw, Square } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { AgentStatusBadge } from '../components/StatusDot'
import { getAgents } from '../data/mock'
import { useMock } from '../data/useMock'
import type { AgentStatus, AgentSummary } from '../data/types'

function nextStatus(action: 'start' | 'stop' | 'restart'): AgentStatus {
  if (action === 'stop') return 'offline'
  if (action === 'start') return 'online'
  return 'working'
}

export function AgentsPage() {
  const { data, loading } = useMock(getAgents)
  const [overrides, setOverrides] = useState<Record<string, AgentStatus>>({})

  function applyAction(agent: AgentSummary, action: 'start' | 'stop' | 'restart') {
    setOverrides((prev) => ({ ...prev, [agent.id]: nextStatus(action) }))
  }

  const agents = data?.map((agent) => ({ ...agent, status: overrides[agent.id] ?? agent.status })) ?? []

  return (
    <>
      <SectionHeader
        icon={Bot}
        title="KI-Agenten"
        subtitle="Executive Agent + 6 Fachagenten - Status, Steuerung und letzte Aktivitaet"
      />

      {loading ? (
        <LoadingState />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {agents.map((agent) => (
            <GlassCard key={agent.id} glow={agent.status === 'working'}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl border"
                    style={{ borderColor: `${agent.color}40`, background: `${agent.color}18` }}
                  >
                    <Bot className="h-4.5 w-4.5" style={{ color: agent.color }} strokeWidth={1.75} />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{agent.name}</div>
                    <div className="text-xs text-white/40">{agent.role}</div>
                  </div>
                </div>
                <AgentStatusBadge status={agent.status} />
              </div>

              <div className="mt-4 min-h-10 text-sm text-white/60">
                {agent.currentTask ?? <span className="text-white/30">Keine aktive Aufgabe</span>}
              </div>

              <div className="mt-3 flex items-center justify-between border-t border-white/10 pt-3 text-xs text-white/40">
                <span>Letzte Aktivitaet: {agent.lastActivity}</span>
                <span>{agent.tasksCompletedToday} Aufgaben heute</span>
              </div>

              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => applyAction(agent, 'start')}
                  disabled={agent.status === 'online' || agent.status === 'working'}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-[color:var(--color-ok)]/25 bg-[color:var(--color-ok)]/10 py-1.5 text-xs text-[color:var(--color-ok)] transition-colors hover:bg-[color:var(--color-ok)]/20 disabled:cursor-not-allowed disabled:opacity-30"
                >
                  <Play className="h-3 w-3" strokeWidth={2} />
                  Start
                </button>
                <button
                  onClick={() => applyAction(agent, 'restart')}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-[color:var(--color-neon-blue)]/25 bg-[color:var(--color-neon-blue)]/10 py-1.5 text-xs text-[color:var(--color-neon-blue)] transition-colors hover:bg-[color:var(--color-neon-blue)]/20"
                >
                  <RotateCw className="h-3 w-3" strokeWidth={2} />
                  Neustart
                </button>
                <button
                  onClick={() => applyAction(agent, 'stop')}
                  disabled={agent.status === 'offline'}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-[color:var(--color-neon-red)]/25 bg-[color:var(--color-neon-red)]/10 py-1.5 text-xs text-[color:var(--color-neon-red)] transition-colors hover:bg-[color:var(--color-neon-red)]/20 disabled:cursor-not-allowed disabled:opacity-30"
                >
                  <Square className="h-3 w-3" strokeWidth={2} />
                  Stopp
                </button>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </>
  )
}
