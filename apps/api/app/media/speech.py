"""Speech-to-text (OpenAI Whisper) and text-to-speech (ElevenLabs)."""
import io

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings


async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("Spracherkennung ist nicht konfiguriert (OPENAI_API_KEY fehlt).")

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename
    transcription = await client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcription.text


def tts_configured() -> bool:
    return bool(get_settings().ELEVENLABS_API_KEY)


async def synthesize_speech(text: str) -> bytes:
    settings = get_settings()
    if not settings.ELEVENLABS_API_KEY:
        raise RuntimeError("Sprachausgabe ist nicht konfiguriert (ELEVENLABS_API_KEY fehlt).")

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}",
            headers={
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )
        resp.raise_for_status()
        return resp.content
