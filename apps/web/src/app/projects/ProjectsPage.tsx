import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Project } from '@/types/projects'

const STATUS_LABEL: Record<Project['status'], string> = {
  active: 'Aktiv',
  paused: 'Pausiert',
  done: 'Erledigt',
  archived: 'Archiviert',
}

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName] = useState('')
  const [creating, setCreating] = useState(false)

  async function load() {
    setProjects(await api.get<Project[]>('/projects'))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate() {
    if (!name.trim()) return
    setCreating(true)
    try {
      await api.post('/projects', { name: name.trim() })
      setName('')
      await load()
    } finally {
      setCreating(false)
    }
  }

  async function handleStatusChange(project: Project, status: Project['status']) {
    await api.patch(`/projects/${project.id}`, { status })
    await load()
  }

  async function handleDelete(id: string) {
    await api.delete(`/projects/${id}`)
    await load()
  }

  return (
    <>
      <PageHeader title="Projekte" subtitle="Deine laufenden Vorhaben" />

      <div className="mb-4 flex gap-2">
        <Input
          placeholder="Neues Projekt..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
        />
        <Button onClick={handleCreate} disabled={creating || !name.trim()}>
          Anlegen
        </Button>
      </div>

      {projects.length === 0 && <p className="text-sm text-text-low">Noch keine Projekte.</p>}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((p) => (
          <Card key={p.id}>
            <div className="flex items-start justify-between">
              <div className="text-sm font-medium text-text-hi">{p.name}</div>
              <button onClick={() => handleDelete(p.id)} className="text-xs text-text-mid hover:text-danger">
                Loeschen
              </button>
            </div>
            {p.description && <p className="mt-1 text-sm text-text-mid">{p.description}</p>}
            <select
              value={p.status}
              onChange={(e) => handleStatusChange(p, e.target.value as Project['status'])}
              className="mt-3 rounded-md border border-border bg-panel-2 px-2 py-1 text-xs text-text-hi"
            >
              {Object.entries(STATUS_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </Card>
        ))}
      </div>
    </>
  )
}
