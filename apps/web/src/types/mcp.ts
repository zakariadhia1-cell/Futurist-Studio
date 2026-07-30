export interface McpServerEntry {
  id: string
  name: string
  transport: 'stdio' | 'sse'
  command: string | null
  args: string[]
  url: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface McpToolInfo {
  name: string
  description: string | null
}
