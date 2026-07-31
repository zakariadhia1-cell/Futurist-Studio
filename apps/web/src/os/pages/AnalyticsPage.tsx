import { BarChart3 } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { AreaTrend, BarComparison, DonutStat } from '../components/charts'
import { getAgentUtilization, getPerformanceSeries, getRevenueSeries, getTaskStats } from '../data/mock'
import { useMock } from '../data/useMock'

export function AnalyticsPage() {
  const { data: revenue, loading: revenueLoading } = useMock(getRevenueSeries)
  const { data: utilization, loading: utilLoading } = useMock(getAgentUtilization)
  const { data: taskStats, loading: taskLoading } = useMock(getTaskStats)
  const { data: perf, loading: perfLoading } = useMock(getPerformanceSeries)

  return (
    <>
      <SectionHeader icon={BarChart3} title="Analysen" subtitle="Umsatzentwicklung, Agentenauslastung, Aufgabenstatistik und Performance" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2" glow>
          <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-white/45">Umsatzentwicklung (30 Tage)</div>
          {revenueLoading || !revenue ? <LoadingState /> : <AreaTrend data={revenue} color="var(--color-neon-blue)" height={220} />}
        </GlassCard>

        <GlassCard>
          <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-white/45">Aufgabenstatistik</div>
          {taskLoading || !taskStats ? (
            <LoadingState />
          ) : (
            <>
              <DonutStat data={taskStats} height={160} />
              <div className="mt-3 space-y-1.5">
                {taskStats.map((entry, index) => (
                  <div key={entry.label} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2 text-white/60">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ background: ['var(--color-neon-blue)', 'var(--color-neon-cyan)', 'var(--color-neon-violet)'][index % 3] }}
                      />
                      {entry.label}
                    </span>
                    <span className="text-white/80">{entry.value}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </GlassCard>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlassCard>
          <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-white/45">Agentenauslastung</div>
          {utilLoading || !utilization ? (
            <LoadingState />
          ) : (
            <BarComparison
              data={utilization.map((u) => ({ label: u.agent, value: u.utilizationPercent }))}
              xKey="label"
              dataKey="value"
              color="var(--color-neon-cyan)"
              layout="vertical"
              height={240}
            />
          )}
        </GlassCard>

        <GlassCard>
          <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-white/45">System-Performance (Anfragen/Std.)</div>
          {perfLoading || !perf ? <LoadingState /> : <AreaTrend data={perf} color="var(--color-neon-violet)" height={240} />}
        </GlassCard>
      </div>
    </>
  )
}
