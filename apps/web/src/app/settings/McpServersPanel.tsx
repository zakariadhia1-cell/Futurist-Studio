import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api, ApiError } from '@/lib/api'
import type { McpServerEntry, McpToolInfo } from '@/types/mcp'

export function McpServersPanel() {
  const [servers, setServers] = useState<McpServerEntry[]>([])
  const [name, setName] = useState('')
  const [transport, setTransport] = useState<'stdio' | 'sse'>('stdio')
  const [command, setCommand] = useState('')
  const [args, setArgs] = useState('')
  const [url, setUrl] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [toolsByServer, setToolsByServer] = useState<Record<string, McpToolInfo[] | string>>({})

  async function load() {
    setServers(await api.get<McpServerEntry[]>('/mcp/servers'))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate() {
    if (!name.trim()) return
    setCreating(true)
    setError(null)
    try {
      await api.post('/mcp/servers', {
        name: name.trim(),
        transport,
        command: transport === 'stdio' ? command.trim() : undefined,
        args: transport === 'stdio' && args.trim() ? args.trim().split(/\s+/) : [],
        url: transport === 'sse' ? url.trim() : undefined,
      })
      setName('')
      setCommand('')
      setArgs('')
      setUrl('')
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'MCP-Server konnte nicht angelegt werden.')
    } finally {
      setCreating(false)
    }
  }

  async function toggleEnabled(server: McpServerEntry) {
    await api.patch(`/mcp/servers/${server.id}`, { enabled: !server.enabled })
    await load()
  }

  async function handleDelete(id: string) {
    await api.delete(`/mcp/servers/${id}`)
    await load()
  }

  async function handleTestTools(id: string) {
    setToolsByServer((prev) => ({ ...prev, [id]: 'Teste...' }))
    try {
      const tools = await api.get<McpToolInfo[]>(`/mcp/servers/${id}/tools`)
      setToolsByServer((prev) => ({ ...prev, [id]: tools }))
    } catch (err) {
      setToolsByServer((prev) => ({
        ...prev,
        [id]: err instanceof ApiError ? err.detail : 'Verbindung fehlgeschlagen.',
      }))
    }
  }

  return (
    <Card className="mt-4 max-w-lg">
      <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">MCP-Server</div>
      <p className="mt-2 text-sm text-text-mid">
        MCP-Server sind das Erweiterungssystem von FUTURIST OS - der Automation Agent kann ihre Tools
        entdecken und aufrufen.
      </p>

      <div className="mt-3 space-y-2">
        <Input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <select
          value={transport}
          onChange={(e) => setTransport(e.target.value as 'stdio' | 'sse')}
          className="w-full rounded-md border border-border bg-panel-2 px-3 py-2 text-sm text-text-hi outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/40"
        >
          <option value="stdio">stdio (lokaler Prozess)</option>
          <option value="sse">sse (Remote-URL)</option>
        </select>
        {transport === 'stdio' ? (
          <>
            <Input placeholder="Befehl, z.B. npx" value={command} onChange={(e) => setCommand(e.target.value)} />
            <Input
              placeholder="Argumente (leerzeichengetrennt)"
              value={args}
              onChange={(e) => setArgs(e.target.value)}
            />
          </>
        ) : (
          <Input placeholder="https://..." value={url} onChange={(e) => setUrl(e.target.value)} />
        )}
        <Button onClick={handleCreate} disabled={creating || !name.trim()}>
          {creating ? 'Lege an...' : 'Server hinzufuegen'}
        </Button>
        {error && <p className="text-sm text-danger">{error}</p>}
      </div>

      {servers.length === 0 && <p className="mt-3 text-sm text-text-low">Noch keine MCP-Server konfiguriert.</p>}
      <div className="mt-3 space-y-2">
        {servers.map((s) => (
          <div key={s.id} className="rounded-md border border-border bg-panel px-3 py-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-text-hi">{s.name}</div>
                <div className="font-mono text-[10px] text-text-low">
                  {s.transport} · {s.transport === 'stdio' ? `${s.command} ${s.args.join(' ')}` : s.url}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1 text-xs text-text-mid">
                  <input type="checkbox" checked={s.enabled} onChange={() => toggleEnabled(s)} />
                  aktiv
                </label>
                <button
                  onClick={() => handleTestTools(s.id)}
                  className="text-xs text-text-mid hover:text-accent"
                >
                  Tools testen
                </button>
                <button onClick={() => handleDelete(s.id)} className="text-xs text-text-mid hover:text-danger">
                  Loeschen
                </button>
              </div>
            </div>
            {toolsByServer[s.id] && (
              <div className="mt-2 border-t border-border-soft pt-2 text-xs text-text-mid">
                {typeof toolsByServer[s.id] === 'string' ? (
                  toolsByServer[s.id] as string
                ) : (
                  <ul className="space-y-1">
                    {(toolsByServer[s.id] as McpToolInfo[]).map((t) => (
                      <li key={t.name}>
                        <span className="text-text-hi">{t.name}</span>
                        {t.description ? ` - ${t.description}` : ''}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  )
}
