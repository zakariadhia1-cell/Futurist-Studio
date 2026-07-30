import { useEffect, useRef, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { connectChatSocket, sendUserMessage } from '@/lib/chat-socket'
import { speak } from '@/lib/voice'
import { useAuthStore } from '@/store/auth-store'
import type { ChatMessage, Conversation } from '@/types/chat'

export function ChatPage() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [status, setStatus] = useState<'connecting' | 'ready' | 'sending' | 'error'>('connecting')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [voiceReplies, setVoiceReplies] = useState(false)
  const [listening, setListening] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(true)
  const socketRef = useRef<WebSocket | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  // Mirrors `streamingText` for synchronous reads in onDone. Needed because onDone must
  // read "the text streamed so far" as a plain side effect - stashing that read inside a
  // setStreamingText(prev => ...) updater looks tempting, but React (Strict Mode, in dev)
  // invokes updater functions twice to catch exactly this: a side effect (setMessages)
  // hidden inside an updater fires twice and duplicates the message.
  const streamingRef = useRef('')
  // The onDone closure below is created once (the effect's deps are [accessToken] only,
  // so the WS connection isn't torn down and rebuilt every time voiceReplies changes) -
  // reading `voiceReplies` directly there would use whatever value existed at mount time
  // forever. Mirroring it into a ref keeps onDone reading the current value.
  const voiceRepliesRef = useRef(voiceReplies)
  voiceRepliesRef.current = voiceReplies

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
            if (voiceRepliesRef.current) speak(finalText, accessToken)
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

  useEffect(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition ?? window.webkitSpeechRecognition
    setSpeechSupported(!!SpeechRecognitionCtor)
  }, [])

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

  function handleMicClick() {
    const SpeechRecognitionCtor = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!SpeechRecognitionCtor) return

    const recognition = new SpeechRecognitionCtor()
    recognition.lang = 'de-DE'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)
    recognition.onresult = (event) => {
      const said = event.results[0][0].transcript
      setDraft(said)
    }
    recognition.start()
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <PageHeader title="Chat" subtitle="Executive Agent" />

      <label className="mb-2 flex items-center gap-2 text-xs text-text-mid">
        <input type="checkbox" checked={voiceReplies} onChange={(e) => setVoiceReplies(e.target.checked)} />
        Antworten vorlesen
      </label>

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
        {speechSupported && (
          <Button
            variant={listening ? 'primary' : 'ghost'}
            onClick={handleMicClick}
            disabled={status !== 'ready'}
            title="Spracheingabe"
          >
            {listening ? '● Hoere...' : '🎤'}
          </Button>
        )}
        <Button onClick={handleSend} disabled={status !== 'ready' || !draft.trim()}>
          Senden
        </Button>
      </div>
    </div>
  )
}
