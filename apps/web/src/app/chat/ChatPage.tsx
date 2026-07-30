import { useEffect, useRef, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { connectChatSocket, sendUserMessage } from '@/lib/chat-socket'
import { useAuthStore } from '@/store/auth-store'
import type { ChatMessage, Conversation } from '@/types/chat'

export function ChatPage() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [status, setStatus] = useState<'connecting' | 'ready' | 'sending' | 'error'>('connecting')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const socketRef = useRef<WebSocket | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  // Mirrors `streamingText` for synchronous reads in onDone. Needed because onDone must
  // read "the text streamed so far" as a plain side effect - stashing that read inside a
  // setStreamingText(prev => ...) updater looks tempting, but React (Strict Mode, in dev)
  // invokes updater functions twice to catch exactly this: a side effect (setMessages)
  // hidden inside an updater fires twice and duplicates the message.
  const streamingRef = useRef('')

  useEffect(() => {
    let cancelled = false
    let socket: WebSocket | null = null

    async function init() {
      const existing = await api.get<Conversation[]>('/conversations')
      let active = existing[0]
      if (!active) {
        active = await api.post<Conversation>('/conversations', { agent_slug: 'executive' })
      }
      if (cancelled || !accessToken) return

      const history = await api.get<ChatMessage[]>(`/conversations/${active.id}/messages`)
      if (cancelled) return
      setMessages(history)

      socket = connectChatSocket(active.id, accessToken, {
        onToken: (text) => {
          streamingRef.current += text
          setStreamingText(streamingRef.current)
        },
        onDone: () => {
          const finalText = streamingRef.current
          if (finalText) {
            setMessages((prev) => [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: finalText,
                created_at: new Date().toISOString(),
              },
            ])
          }
          streamingRef.current = ''
          setStreamingText('')
          setStatus('ready')
        },
        onError: (message) => {
          setErrorMessage(message)
          setStatus('ready')
        },
      })
      if (cancelled) {
        socket.close()
        return
      }
      socket.onopen = () => setStatus('ready')
      socket.onclose = () => setStatus((prev) => (prev === 'ready' ? 'error' : prev))
      socketRef.current = socket
    }

    init()
    return () => {
      cancelled = true
      socket?.close()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages, streamingText])

  function handleSend() {
    const content = draft.trim()
    if (!content || !socketRef.current || status !== 'ready') return
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', content, created_at: new Date().toISOString() },
    ])
    sendUserMessage(socketRef.current, content)
    setDraft('')
    setErrorMessage(null)
    setStatus('sending')
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <PageHeader title="Chat" subtitle="Executive Agent" />

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-border bg-panel p-4">
        {messages.length === 0 && !streamingText && (
          <p className="text-sm text-text-low">Noch keine Nachrichten. Schreib etwas an den Executive Agent.</p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <div
              className={
                m.role === 'user'
                  ? 'max-w-[75%] rounded-lg bg-accent-soft px-3 py-2 text-sm text-text-hi'
                  : 'max-w-[75%] rounded-lg bg-panel-2 px-3 py-2 text-sm text-text-hi'
              }
            >
              {m.content}
            </div>
          </div>
        ))}
        {streamingText && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-lg bg-panel-2 px-3 py-2 text-sm text-text-hi">
              {streamingText}
              <span className="animate-pulse">▍</span>
            </div>
          </div>
        )}
      </div>

      {errorMessage && <p className="mt-2 text-sm text-danger">{errorMessage}</p>}
      {status === 'connecting' && <p className="mt-2 text-xs text-text-low">Verbinde...</p>}

      <div className="mt-3 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Nachricht an den Executive Agent..."
          disabled={status !== 'ready'}
          className="flex-1 rounded-md border border-border bg-panel-2 px-3 py-2 text-sm text-text-hi placeholder:text-text-low outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/40 disabled:opacity-50"
        />
        <Button onClick={handleSend} disabled={status !== 'ready' || !draft.trim()}>
          Senden
        </Button>
      </div>
    </div>
  )
}
