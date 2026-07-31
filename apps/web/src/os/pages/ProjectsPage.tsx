import { FolderKanban } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { ProgressBar } from '../components/ProgressBar'
import { Badge, type BadgeTone } from '../components/Badge'
import { getProjects } from '../data/mock'
import { useMock } from '../data/useMock'
import type { ProjectState } from '../data/types'

const STATE_LABEL: Record<ProjectState, string> = {
  active: 'Aktiv',
  paused: 'Pausiert',
  done: 'Erledigt',
  at_risk: 'Gefaehrdet',
}

const STATE_TONE: Record<ProjectState, BadgeTone> = {
  active: 'info',
  paused: 'neutral',
  done: 'ok',
  at_risk: 'danger',
}

export function ProjectsPage() {
  const { data: projects, loading } = useMock(getProjects)

  return (
    <>
      <SectionHeader icon={FolderKanban} title="Projekte" subtitle="Alle laufenden Vorhaben mit Fortschritt und verantwortlichem Agenten" />

      {loading || !projects ? (
        <LoadingState />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {projects.map((project) => (
            <GlassCard key={project.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: project.color, boxShadow: `0 0 8px ${project.color}` }} />
                  <div className="text-sm font-medium text-white">{project.name}</div>
                </div>
                <Badge tone={STATE_TONE[project.state]}>{STATE_LABEL[project.state]}</Badge>
              </div>

              <div className="mt-4">
                <div className="mb-1.5 flex items-center justify-between text-xs text-white/55">
                  <span>Fortschritt</span>
                  <span>{project.percentComplete}%</span>
                </div>
                <ProgressBar percent={project.percentComplete} tone={project.state === 'at_risk' ? 'red' : 'blue'} />
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3 text-xs text-white/40">
                <span>Verantwortlich: {project.responsibleAgent}</span>
                <span>{project.lastChange}</span>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </>
  )
}
