import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { clsx } from '@/lib/clsx'
import type { Task } from '@/types/projects'

const PRIORITY_COLOR: Record<Task['priority'], string> = {
  low: 'text-text-low',
  medium: 'text-text-mid',
  high: 'text-danger',
}

export function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [title, setTitle] = useState('')
  const [creating, setCreating] = useState(false)

  async function load() {
    setTasks(await api.get<Task[]>('/tasks'))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate() {
    if (!title.trim()) return
    setCreating(true)
    try {
      await api.post('/tasks', { title: title.trim() })
      setTitle('')
      await load()
    } finally {
      setCreating(false)
    }
  }

  async function toggleDone(task: Task) {
    await api.patch(`/tasks/${task.id}`, { status: task.status === 'done' ? 'todo' : 'done' })
    await load()
  }

  async function handleDelete(id: string) {
    await api.delete(`/tasks/${id}`)
    await load()
  }

  return (
    <>
      <PageHeader title="Aufgaben" subtitle="Deine To-Dos" />

      <div className="mb-4 flex gap-2">
        <Input
          placeholder="Neue Aufgabe..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
        />
        <Button onClick={handleCreate} disabled={creating || !title.trim()}>
          Anlegen
        </Button>
      </div>

      {tasks.length === 0 && <p className="text-sm text-text-low">Noch keine Aufgaben.</p>}
      <div className="space-y-2">
        {tasks.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between rounded-md border border-border bg-panel px-3 py-2"
          >
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={t.status === 'done'} onChange={() => toggleDone(t)} />
              <span
                className={clsx('text-sm text-text-hi', t.status === 'done' && 'line-through text-text-low')}
              >
                {t.title}
              </span>
              <span className={clsx('font-mono text-[10px] uppercase', PRIORITY_COLOR[t.priority])}>
                {t.priority}
              </span>
            </label>
            <button onClick={() => handleDelete(t.id)} className="text-xs text-text-mid hover:text-danger">
              Loeschen
            </button>
          </div>
        ))}
      </div>
    </>
  )
}
