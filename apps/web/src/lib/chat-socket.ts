import type { ServerEnvelope } from '@/types/chat'

export interface ChatSocketHandlers {
  onToken: (text: string) => void
  onDone: () => void
  onError: (message: string) => void
}

export function connectChatSocket(
  conversationId: string,
  accessToken: string,
  handlers: ChatSocketHandlers,
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${window.location.host}/ws/chat/${conversationId}?token=${encodeURIComponent(accessToken)}`
  const socket = new WebSocket(url)

  socket.onmessage = (event) => {
    const envelope: ServerEnvelope = JSON.parse(event.data)
    if (envelope.type === 'token') handlers.onToken(envelope.payload.text)
    else if (envelope.type === 'done') handlers.onDone()
    else if (envelope.type === 'error') handlers.onError(envelope.payload.message)
  }

  return socket
}

export function sendUserMessage(socket: WebSocket, content: string): void {
  socket.send(JSON.stringify({ type: 'user_message', content }))
}
