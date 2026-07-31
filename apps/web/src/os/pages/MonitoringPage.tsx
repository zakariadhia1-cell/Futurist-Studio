import { ActivitySquare, AlertTriangle, CircleAlert, Info } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { Badge, type BadgeTone } from '../components/Badge'
import { AreaTrend } from '../components/charts'
import { getApiStatus, getLogs, getPerformanceSeries } from '../data/mock'
import { useMock } from '../data/useMock'
import type { ApiStatusEntry, LogLevel } from '../data/types'

const LOG_META: Record<LogLevel, { tone: BadgeTone; icon: typeof Info }> = {
  info: { tone: 'neutral', icon: Info },
  warn: { tone: 'warn', icon: AlertTriangle },
  error: { tone: 'danger', icon: CircleAlert },
}

const API_STATUS_TONE: Record<ApiStatusEntry['status'], BadgeTone> = {
  ok: 'ok',
  degraded: 'warn',
  down: 'danger',
}

export function MonitoringPage() {
  const { data: logs, loading: logsLoading } = useMock(getLogs)
  const { data: apiStatus, loading: apiLoading } = useMock(getApiStatus)
  const { data: perf, loading: perfLoading } = useMock(getPerformanceSeries)

  const errorCount = logs?.filter((l) => l.level === 'error').length ?? 0
  const warnCount = logs?.filter((l) => l.level === 'warn').length ?? 0

  return (
    <>
      <SectionHeader icon={ActivitySquare} title="Systemueberwachung" subtitle="Logs, Fehler, Warnungen, Performance und externe API-Verbindungen" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2" glow>
          <div className="mb-2 flex items-center justify-between">
            <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">Latenz (24 Std.)</div>
            <div className="flex gap-3 text-xs">
              <span className="text-[color:var(--color-neon-red)]">{errorCount} Fehler</span>
              <span className="text-[color:var(--color-neon-amber)]">{warnCount} Warnungen</span>
            </div>
          </div>
          {perfLoading || !perf ? <LoadingState /> : <AreaTrend data={perf} color="var(--color-neon-cyan)" />}
        </GlassCard>

        <GlassCard>
          <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">API-Status</div>
          {apiLoading || !apiStatus ? (
            <LoadingState />
          ) : (
            <div className="mt-3 space-y-2.5">
              {apiStatus.map((entry) => (
                <div key={entry.name} className="flex items-center justify-between">
                  <span className="text-sm text-white/75">{entry.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-white/35">{entry.latencyMs}ms</span>
                    <Badge tone={API_STATUS_TONE[entry.status]} dot>
                      {entry.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      <GlassCard className="mt-4" noPadding>
        <div className="p-5 pb-0 font-mono text-[11px] uppercase tracking-wider text-white/45">Live-Logs</div>
        {logsLoading || !logs ? (
          <LoadingState />
        ) : (
          <div className="mt-3 divide-y divide-white/[0.06] font-mono text-xs">
            {logs.map((log) => {
              const meta = LOG_META[log.level]
              const Icon = meta.icon
              return (
                <div key={log.id} className="flex items-start gap-3 px-5 py-2.5">
                  <Icon
                    className="mt-0.5 h-3.5 w-3.5 shrink-0"
                    style={{
                      color:
                        log.level === 'error'
                          ? 'var(--color-neon-red)'
                          : log.level === 'warn'
                            ? 'var(--color-neon-amber)'
                            : 'rgba(255,255,255,0.35)',
                    }}
                  />
                  <span className="w-28 shrink-0 text-white/35">{log.service}</span>
                  <span className="flex-1 text-white/70">{log.message}</span>
                  <span className="shrink-0 text-white/25">{log.timestamp}</span>
                </div>
              )
            })}
          </div>
        )}
        <div className="p-3" />
      </GlassCard>
    </>
  )
}
