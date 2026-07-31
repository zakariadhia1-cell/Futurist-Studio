import { useEffect, useRef, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import type { FileEntry } from '@/types/files'

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function FilesPage() {
  const [files, setFiles] = useState<FileEntry[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function load() {
    setFiles(await api.get<FileEntry[]>('/files'))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleUpload(fileList: FileList | null) {
    const file = fileList?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('upload', file)
      await api.upload('/files', formData)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload fehlgeschlagen.')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function handleDownload(file: FileEntry) {
    const blob = await api.downloadBlob(`/files/${file.id}/download`)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = file.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  async function handleDelete(id: string) {
    await api.delete(`/files/${id}`)
    await load()
  }

  return (
    <>
      <PageHeader title="Dateien" subtitle="Hochgeladene und von Agenten erzeugte Dateien" />

      <div className="mb-4 flex items-center gap-2">
        <input ref={inputRef} type="file" className="hidden" onChange={(e) => handleUpload(e.target.files)} />
        <Button onClick={() => inputRef.current?.click()} disabled={uploading}>
          {uploading ? 'Lade hoch...' : 'Datei hochladen'}
        </Button>
        {error && <span className="text-sm text-danger">{error}</span>}
      </div>

      {files.length === 0 && <p className="text-sm text-text-low">Noch keine Dateien.</p>}
      <div className="space-y-2">
        {files.map((f) => (
          <div
            key={f.id}
            className="flex items-center justify-between rounded-md border border-border bg-panel px-3 py-2"
          >
            <div>
              <div className="text-sm text-text-hi">{f.filename}</div>
              <div className="font-mono text-[10px] text-text-low">
                {f.content_type} · {formatSize(f.size_bytes)} · {f.source}
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => handleDownload(f)} className="text-xs text-text-mid hover:text-accent">
                Herunterladen
              </button>
              <button onClick={() => handleDelete(f.id)} className="text-xs text-text-mid hover:text-danger">
                Loeschen
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
