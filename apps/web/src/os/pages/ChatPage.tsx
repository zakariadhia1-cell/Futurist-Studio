import { useEffect, useRef, useState } from 'react'
import { Code2, FileUp, ImageIcon, Mic, MessageSquare, Paperclip, Send, Sparkles, X } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { getChatHistory } from '../data/mock'
import { useMock } from '../data/useMock'
import type { ChatMessage } from '../data/types'

const CANNED_REPLIES = [
  'Verstanden - ich delegiere das an den passenden Fachagenten und melde mich mit dem Ergebnis.',
  'Ich habe die Anfrage analysiert. Soll ich einen konkreten Loesungsvorschlag ausarbeiten?',
  'Erledigt. Ich habe die Aenderung im Hintergrund vorbereitet, sie wartet auf deine Freigabe.',
]

function isImageFile(file: File) {
  return file.type.startsWith('image/')
}

function isCodeFile(file: File) {
  return /\.(py|ts|tsx|js|jsx|go|rs|java|rb|sql|json|yaml|yml)$/i.test(file.name)
}

export function ChatPage() {
  const { data: history } = useMock(getChatHistory)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [pendingFile, setPendingFile] = useState<{ name: string; kind: 'bild' | 'code' | 'datei' } | null>(null)
  const [listening, setListening] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (history) setMessages(history)
  }, [history])

  useEffect(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition ?? window.webkitSpeechRecognition
    setSpeechSupported(!!SpeechRecognitionCtor)
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

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
    recognition.onresult = (event) => setDraft(event.results[0][0].transcript)
    recognition.start()
  }

  function handleFileChosen(file: File) {
    setPendingFile({ name: file.name, kind: isImageFile(file) ? 'bild' : isCodeFile(file) ? 'code' : 'datei' })
  }

  function handleSend() {
    if (!draft.trim() && !pendingFile) return
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: draft.trim() || `Analysiere bitte: ${pendingFile?.name}`,
      attachmentLabel: pendingFile?.name,
      createdAt: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages((prev) => [...prev, userMessage])
    setDraft('')
    setPendingFile(null)

    window.setTimeout(() => {
      const reply = CANNED_REPLIES[Math.floor(Math.random() * CANNED_REPLIES.length)]
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: reply,
          createdAt: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    }, 700)
  }

  return (
    <div className="flex h-[calc(100vh-8.5rem)] flex-col">
      <SectionHeader icon={MessageSquare} title="KI-Chat" subtitle="Direkter Draht zum Executive Agent - Text, Sprache, Datei- und Bildanalyse" />

      <GlassCard noPadding className="flex min-h-0 flex-1 flex-col" glow>
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                  message.role === 'user'
                    ? 'bg-[color:var(--color-neon-blue)]/15 text-white border border-[color:var(--color-neon-blue)]/25'
                    : 'bg-white/[0.05] text-white/85 border border-white/10'
                }`}
              >
                {message.attachmentLabel && (
                  <div className="mb-1.5 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-white/40">
                    <Paperclip className="h-3 w-3" /> {message.attachmentLabel}
                  </div>
                )}
                <div>{message.content}</div>
                <div className="mt-1 text-right font-mono text-[10px] text-white/30">{message.createdAt}</div>
              </div>
            </div>
          ))}
        </div>

        {pendingFile && (
          <div className="mx-5 mb-2 flex items-center gap-2 rounded-lg border border-[color:var(--color-neon-blue)]/25 bg-[color:var(--color-neon-blue)]/10 px-3 py-1.5 text-xs text-white/70">
            {pendingFile.kind === 'bild' ? <ImageIcon className="h-3.5 w-3.5" /> : pendingFile.kind === 'code' ? <Code2 className="h-3.5 w-3.5" /> : <FileUp className="h-3.5 w-3.5" />}
            <span className="flex-1 truncate">{pendingFile.name}</span>
            <button onClick={() => setPendingFile(null)} className="text-white/40 hover:text-white">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        <div className="flex items-center gap-2 border-t border-white/10 p-4">
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFileChosen(file)
              e.target.value = ''
            }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Datei / Bild / Code anhaengen"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 text-white/50 transition-colors hover:bg-white/[0.06] hover:text-white"
          >
            <Paperclip className="h-4 w-4" strokeWidth={1.75} />
          </button>
          {speechSupported && (
            <button
              onClick={handleMicClick}
              title="Spracheingabe"
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border transition-colors ${
                listening
                  ? 'border-[color:var(--color-neon-red)]/40 bg-[color:var(--color-neon-red)]/10 text-[color:var(--color-neon-red)]'
                  : 'border-white/10 text-white/50 hover:bg-white/[0.06] hover:text-white'
              }`}
            >
              <Mic className="h-4 w-4" strokeWidth={1.75} />
            </button>
          )}
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Nachricht an Jarvis..."
            className="flex-1 rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-[color:var(--color-neon-blue)]/40"
          />
          <button
            onClick={handleSend}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[color:var(--color-neon-blue)]/40 bg-[color:var(--color-neon-blue)]/15 text-[color:var(--color-neon-blue)] transition-colors hover:bg-[color:var(--color-neon-blue)]/25"
          >
            <Send className="h-4 w-4" strokeWidth={1.75} />
          </button>
        </div>
      </GlassCard>

      <div className="mt-3 flex items-center gap-2 text-xs text-white/30">
        <Sparkles className="h-3.5 w-3.5" strokeWidth={1.75} />
        Spracheingabe nutzt die Web Speech API des Browsers. Datei-, Bild- und Codeanalyse sind hier als UI vorbereitet - die
        Auswertung laeuft ueber den bestehenden Chat unter "Chat" im Hauptmenue (Vision-/OCR-Endpunkte, Phase 6).
      </div>
    </div>
  )
}
