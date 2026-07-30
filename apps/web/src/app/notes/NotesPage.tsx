import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Note } from '@/types/files'

export function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([])
  const [title, setTitle] = useState('')
  const [creating, setCreating] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [draftContent, setDraftContent] = useState('')
  const [saving, setSaving] = useState(false)

  const selected = notes.find((n) => n.id === selectedId) ?? null

  async function load() {
    const loaded = await api.get<Note[]>('/notes')
    setNotes(loaded)
    return loaded
  }

  useEffect(() => {
    load()
  }, [])

  function selectNote(note: Note) {
    setSelectedId(note.id)
    setDraftContent(note.content)
  }

  async function handleCreate() {
    if (!title.trim()) return
    setCreating(true)
    try {
      const note = await api.post<Note>('/notes', { title: title.trim() })
      setTitle('')
      await load()
      selectNote(note)
    } finally {
      setCreating(false)
    }
  }

  async function handleSave() {
    if (!selected) return
    setSaving(true)
    try {
      await api.patch(`/notes/${selected.id}`, { content: draftContent })
      await load()
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/notes/${id}`)
    if (selectedId === id) {
      setSelectedId(null)
      setDraftContent('')
    }
    await load()
  }

  return (
    <>
      <PageHeader title="Notizen" subtitle="Freitext-Notizen" />

      <div className="mb-4 flex gap-2">
        <Input
          placeholder="Neue Notiz..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
        />
        <Button onClick={handleCreate} disabled={creating || !title.trim()}>
          Anlegen
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-2 lg:col-span-1">
          {notes.length === 0 && <p className="text-sm text-text-low">Noch keine Notizen.</p>}
          {notes.map((n) => (
            <div
              key={n.id}
              onClick={() => selectNote(n)}
              className={`flex cursor-pointer items-center justify-between rounded-md border px-3 py-2 ${
                n.id === selectedId ? 'border-accent bg-accent-soft' : 'border-border bg-panel'
              }`}
            >
              <span className="text-sm text-text-hi">{n.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete(n.id)
                }}
                className="text-xs text-text-mid hover:text-danger"
              >
                Loeschen
              </button>
            </div>
          ))}
        </div>

        <Card className="lg:col-span-2">
          {selected ? (
            <div className="space-y-3">
              <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">{selected.title}</div>
              <textarea
                value={draftContent}
                onChange={(e) => setDraftContent(e.target.value)}
                rows={12}
                className="w-full rounded-md border border-border bg-panel-2 px-3 py-2 text-sm text-text-hi placeholder:text-text-low outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/40"
              />
              <Button onClick={handleSave} disabled={saving}>
                {saving ? 'Speichere...' : 'Speichern'}
              </Button>
            </div>
          ) : (
            <p className="text-sm text-text-low">Waehle eine Notiz aus oder lege eine neue an.</p>
          )}
        </Card>
      </div>
    </>
  )
}
