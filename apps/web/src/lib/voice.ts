/** Plays TTS audio for `text` via the backend (ElevenLabs) if configured, otherwise
 * falls back to the browser's built-in speechSynthesis - so voice output always works,
 * just at lower quality without an ElevenLabs key. */
export async function speak(text: string, accessToken: string | null): Promise<void> {
  if (accessToken) {
    try {
      const resp = await fetch('/api/v1/voice/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ text }),
      })
      if (resp.ok) {
        const blob = await resp.blob()
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audio.onended = () => URL.revokeObjectURL(url)
        await audio.play()
        return
      }
    } catch {
      // fall through to browser TTS
    }
  }

  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'de-DE'
    window.speechSynthesis.speak(utterance)
  }
}
