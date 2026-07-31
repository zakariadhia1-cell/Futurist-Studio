import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { KnowledgeDocument, SearchChunkResult } from '@/types/knowledge'

export function KnowledgePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [adding, setAdding] = useState(false)

  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchChunkResult[] | null>(null)
  const [searching, setSearching] = useState(false)

  async function loadDocuments() {
    setDocuments(await api.get<KnowledgeDocument[]>('/knowledge/documents'))
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  async function handleAdd() {
    if (!title.trim() || !content.trim()) return
    setAdding(true)
    try {
      await api.post('/knowledge/documents', { title: title.trim(), content: content.trim() })
      setTitle('')
      setContent('')
      await loadDocuments()
    } finally {
      setAdding(false)
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/knowledge/documents/${id}`)
    await loadDocuments()
  }

  async function handleSearch() {
    if (!query.trim()) return
    setSearching(true)
    try {
      const response = await api.post<{ results: SearchChunkResult[] }>('/knowledge/search', {
        query: query.trim(),
      })
      setResults(response.results)
    } finally {
      setSearching(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Wissensdatenbank"
        subtitle="Dokumente und Notizen, die Jarvis im Chat als Kontext nutzt"
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">Dokument hinzufuegen</div>
          <div className="mt-3 space-y-2">
            <Input placeholder="Titel" value={title} onChange={(e) => setTitle(e.target.value)} />
            <textarea
              placeholder="Inhalt..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={5}
              className="w-full rounded-md border border-border bg-panel-2 px-3 py-2 text-sm text-text-hi placeholder:text-text-low outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/40"
            />
            <Button onClick={handleAdd} disabled={adding || !title.trim() || !content.trim()}>
              {adding ? 'Speichere...' : 'Speichern'}
            </Button>
          </div>
        </Card>

        <Card>
          <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">Semantische Suche</div>
          <div className="mt-3 flex gap-2">
            <Input
              placeholder="Wonach suchst du?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={searching || !query.trim()}>
              Suchen
            </Button>
          </div>
          {results && (
            <div className="mt-3 space-y-2">
              {results.length === 0 && <p className="text-sm text-text-low">Keine Treffer.</p>}
              {results.map((r, i) => (
                <div key={i} className="rounded-md border border-border-soft bg-panel-2 p-2 text-sm">
                  <div className="font-mono text-[10px] text-text-low">
                    {r.document_title} · Distanz {r.distance.toFixed(3)}
                  </div>
                  <div className="text-text-mid">{r.content}</div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-text-low">Dokumente</div>
        {documents.length === 0 && <p className="text-sm text-text-low">Noch keine Dokumente.</p>}
        <div className="space-y-2">
          {documents.map((d) => (
            <div
              key={d.id}
              className="flex items-center justify-between rounded-md border border-border bg-panel px-3 py-2"
            >
              <div>
                <div className="text-sm text-text-hi">{d.title}</div>
                <div className="font-mono text-[10px] text-text-low">{d.source_type}</div>
              </div>
              <button onClick={() => handleDelete(d.id)} className="text-xs text-text-mid hover:text-danger">
                Loeschen
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
