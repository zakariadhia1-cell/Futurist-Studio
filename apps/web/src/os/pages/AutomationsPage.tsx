import { CheckCircle2, Clock, PlayCircle, Workflow, XCircle } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { StatTile } from '../components/StatTile'
import { Badge, type BadgeTone } from '../components/Badge'
import { getAutomations } from '../data/mock'
import { useMock } from '../data/useMock'
import type { WorkflowStatus } from '../data/types'

const STATUS_META: Record<WorkflowStatus, { label: string; tone: BadgeTone; icon: typeof PlayCircle }> = {
  running: { label: 'Laeuft', tone: 'info', icon: PlayCircle },
  success: { label: 'Erfolgreich', tone: 'ok', icon: CheckCircle2 },
  failed: { label: 'Fehlgeschlagen', tone: 'danger', icon: XCircle },
  scheduled: { label: 'Geplant', tone: 'neutral', icon: Clock },
}

export function AutomationsPage() {
  const { data: workflows, loading } = useMock(getAutomations)

  const totalSuccess = workflows?.reduce((sum, w) => sum + w.successCount7d, 0) ?? 0
  const totalFailed = workflows?.reduce((sum, w) => sum + w.failCount7d, 0) ?? 0
  const running = workflows?.filter((w) => w.status === 'running').length ?? 0

  return (
    <>
      <SectionHeader icon={Workflow} title="Automationen" subtitle="n8n-Workflows, Zeitplaene und Job-Historie der letzten 7 Tage" />

      {loading || !workflows ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatTile label="Laufende Workflows" value={String(running)} icon={PlayCircle} accent="blue" />
            <StatTile label="Erfolgreiche Jobs (7T)" value={String(totalSuccess)} icon={CheckCircle2} accent="cyan" />
            <StatTile label="Fehlgeschlagene Jobs (7T)" value={String(totalFailed)} icon={XCircle} accent="red" />
          </div>

          <div className="mt-4 space-y-3">
            {workflows.map((workflow) => {
              const meta = STATUS_META[workflow.status]
              const Icon = meta.icon
              return (
                <GlassCard key={workflow.id} className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04]">
                      <Icon
                        className={`h-4.5 w-4.5 ${workflow.status === 'running' ? 'animate-pulse' : ''}`}
                        style={{
                          color:
                            meta.tone === 'ok'
                              ? 'var(--color-ok)'
                              : meta.tone === 'danger'
                                ? 'var(--color-neon-red)'
                                : meta.tone === 'info'
                                  ? 'var(--color-neon-blue)'
                                  : 'rgba(255,255,255,0.5)',
                        }}
                        strokeWidth={1.75}
                      />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{workflow.name}</div>
                      <div className="text-xs text-white/40">Trigger: {workflow.trigger}</div>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 sm:gap-6">
                    <div className="text-xs text-white/40">
                      <div>Letzter Lauf: {workflow.lastRun ?? '-'}</div>
                      <div>Naechster Lauf: {workflow.nextRun ?? '-'}</div>
                    </div>
                    <div className="flex gap-2 font-mono text-[10px] text-white/40">
                      <span className="text-[color:var(--color-ok)]">{workflow.successCount7d} OK</span>
                      <span className="text-[color:var(--color-neon-red)]">{workflow.failCount7d} Fehler</span>
                    </div>
                    <Badge tone={meta.tone} dot>
                      {meta.label}
                    </Badge>
                  </div>
                </GlassCard>
              )
            })}
          </div>
        </>
      )}
    </>
  )
}
