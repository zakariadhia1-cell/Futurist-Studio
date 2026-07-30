export interface Agent {
  id: string
  slug: string
  name: string
  description: string | null
}

export interface Conversation {
  id: string
  agent_id: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  created_at: string
}

export type ServerEnvelope =
  | { type: 'token'; payload: { text: string } }
  | { type: 'done'; payload: Record<string, never> }
  | { type: 'error'; payload: { message: string } }
