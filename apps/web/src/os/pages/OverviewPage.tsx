import { Activity, Bot, Cpu, Database, HardDrive, MemoryStick, Wifi } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { StatTile } from '../components/StatTile'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { ProgressBar } from '../components/ProgressBar'
import { AgentStatusBadge } from '../components/StatusDot'
import { Badge } from '../components/Badge'
import { getAgents, getSystemStatus, getTasks } from '../data/mock'
import { useMock } from '../data/useMock'

export function OverviewPage() {
  const { data: system, loading: systemLoading } = useMock(getSystemStatus)
  const { data: agents, loading: agentsLoading } = useMock(getAgents)
  const { data: tasks, loading: tasksLoading } = useMock(getTasks)

  return (
    <>
      <SectionHeader
        icon={Activity}
        title="Systemuebersicht"
        subtitle="Live-Status von FUTURIST OS, Ressourcen und aktiven Agenten"
      />

      {systemLoading || !system ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="CPU-Auslastung" value={`${system.cpuPercent}%`} icon={Cpu} accent="blue" />
            <StatTile
              label="Arbeitsspeicher"
              value={`${system.ramUsedGb.toFixed(1)} / ${system.ramTotalGb} GB`}
              icon={MemoryStick}
              accent="cyan"
            />
            <StatTile
              label="Speicherplatz"
              value={`${system.storageUsedGb} / ${system.storageTotalGb} GB`}
              icon={HardDrive}
              accent="violet"
            />
            <StatTile
              label="Netzwerk"
              value={`${system.networkDownMbps} / ${system.networkUpMbps} Mbps`}
              icon={Wifi}
              accent="amber"
            />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <GlassCard glow>
              <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">Ressourcen im Detail</div>
              <div className="mt-4 space-y-4">
                <div>
                  <div className="mb-1.5 flex items-center justify-between text-xs text-white/60">
                    <span>CPU</span>
                    <span>{system.cpuPercent}%</span>
                  </div>
                  <ProgressBar percent={system.cpuPercent} tone="blue" />
                </div>
                <div>
                  <div className="mb-1.5 flex items-center justify-between text-xs text-white/60">
                    <span>RAM</span>
                    <span>{system.ramPercent}%</span>
                  </div>
                  <ProgressBar percent={system.ramPercent} tone="cyan" />
                </div>
                <div>
                  <div className="mb-1.5 flex items-center justify-between text-xs text-white/60">
                    <span>Speicher</span>
                    <span>{system.storagePercent}%</span>
                  </div>
                  <ProgressBar percent={system.storagePercent} tone="violet" />
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3 text-xs text-white/45">
                <span>Betriebszeit</span>
                <span className="font-mono text-white/70">{system.uptimeHours} Std.</span>
              </div>
            </GlassCard>

            <GlassCard>
              <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">Agenten-Status</div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-semibold text-white">{system.agentsOnline}</span>
                <span className="text-sm text-white/40">/ {system.agentsTotal} online</span>
              </div>
              <div className="mt-4 space-y-2.5">
                {agentsLoading || !agents ? (
                  <LoadingState label="Lade Agenten..." />
                ) : (
                  agents.slice(0, 4).map((agent) => (
                    <div key={agent.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm text-white/75">
                        <Bot className="h-3.5 w-3.5 text-white/35" strokeWidth={1.75} />
                        {agent.name}
                      </div>
                      <AgentStatusBadge status={agent.status} />
                    </div>
                  ))
                )}
              </div>
            </GlassCard>

            <GlassCard>
              <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">Aufgaben-Snapshot</div>
              {tasksLoading || !tasks ? (
                <LoadingState label="Lade Aufgaben..." />
              ) : (
                <>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-3xl font-semibold text-white">{tasks.filter((t) => t.state === 'active').length}</span>
                    <span className="text-sm text-white/40">aktiv</span>
                  </div>
                  <div className="mt-4 space-y-3">
                    {tasks
                      .filter((t) => t.state === 'active')
                      .slice(0, 3)
                      .map((task) => (
                        <div key={task.id}>
                          <div className="mb-1 flex items-center justify-between text-xs text-white/60">
                            <span className="truncate pr-2">{task.title}</span>
                            <span>{task.progress}%</span>
                          </div>
                          <ProgressBar percent={task.progress} tone="blue" height="h-1" />
                        </div>
                      ))}
                  </div>
                  <div className="mt-4 flex gap-2 border-t border-white/10 pt-3">
                    <Badge tone="neutral">{tasks.filter((t) => t.state === 'queued').length} in Warteschlange</Badge>
                    <Badge tone="ok">{tasks.filter((t) => t.state === 'done').length} erledigt</Badge>
                  </div>
                </>
              )}
            </GlassCard>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <GlassCard className="flex items-center gap-3">
              <Database className="h-4 w-4 text-[color:var(--color-ok)]" strokeWidth={1.75} />
              <div>
                <div className="text-sm text-white">Datenbank verbunden</div>
                <div className="text-xs text-white/40">PostgreSQL 16 + pgvector</div>
              </div>
            </GlassCard>
            <GlassCard className="flex items-center gap-3">
              <Activity className="h-4 w-4 text-[color:var(--color-ok)]" strokeWidth={1.75} />
              <div>
                <div className="text-sm text-white">Redis verbunden</div>
                <div className="text-xs text-white/40">Rate-Limiting & Sessions</div>
              </div>
            </GlassCard>
            <GlassCard className="flex items-center gap-3">
              <Wifi className="h-4 w-4 text-[color:var(--color-ok)]" strokeWidth={1.75} />
              <div>
                <div className="text-sm text-white">Alle Systeme betriebsbereit</div>
                <div className="text-xs text-white/40">Keine aktiven Stoerungen</div>
              </div>
            </GlassCard>
          </div>
        </>
      )}
    </>
  )
}
