import { ListChecks } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { ProgressBar } from '../components/ProgressBar'
import { Badge, type BadgeTone } from '../components/Badge'
import { getTasks } from '../data/mock'
import { useMock } from '../data/useMock'
import type { TaskItem, TaskPriority, TaskState } from '../data/types'

const PRIORITY_TONE: Record<TaskPriority, BadgeTone> = { low: 'neutral', medium: 'info', high: 'danger' }
const PRIORITY_LABEL: Record<TaskPriority, string> = { low: 'Niedrig', medium: 'Mittel', high: 'Hoch' }

const COLUMNS: { state: TaskState; title: string; tone: BadgeTone }[] = [
  { state: 'active', title: 'Aktive Aufgaben', tone: 'info' },
  { state: 'queued', title: 'Warteschlange', tone: 'warn' },
  { state: 'done', title: 'Abgeschlossen', tone: 'ok' },
]

function TaskCard({ task }: { task: TaskItem }) {
  return (
    <GlassCard noPadding className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="text-sm font-medium text-white">{task.title}</div>
        <Badge tone={PRIORITY_TONE[task.priority]}>{PRIORITY_LABEL[task.priority]}</Badge>
      </div>
      <div className="mt-2 text-xs text-white/40">{task.agent}</div>
      {task.state !== 'queued' && (
        <div className="mt-3">
          <ProgressBar percent={task.progress} tone={task.state === 'done' ? 'ok' : 'blue'} height="h-1" />
        </div>
      )}
      {task.dueDate && <div className="mt-2.5 font-mono text-[10px] uppercase tracking-wider text-white/35">Faellig: {task.dueDate}</div>}
    </GlassCard>
  )
}

export function TasksPage() {
  const { data: tasks, loading } = useMock(getTasks)

  return (
    <>
      <SectionHeader icon={ListChecks} title="Aufgaben" subtitle="Aktive Arbeit, Warteschlange und abgeschlossene Aufgaben aller Agenten" />

      {loading || !tasks ? (
        <LoadingState />
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          {COLUMNS.map((column) => {
            const items = tasks.filter((t) => t.state === column.state)
            return (
              <div key={column.state}>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-medium text-white/80">{column.title}</h2>
                  <Badge tone={column.tone}>{items.length}</Badge>
                </div>
                <div className="space-y-3">
                  {items.length === 0 && <p className="text-xs text-white/30">Keine Eintraege.</p>}
                  {items.map((task) => (
                    <TaskCard key={task.id} task={task} />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </>
  )
}
