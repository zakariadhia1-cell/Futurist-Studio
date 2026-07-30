"""Text-to-speech via ElevenLabs."""
from typing import Optional

import requests

from jarvis.backend.config import ELEVENLABS_API_KEY, ELEVENLABS_MODEL_ID, ELEVENLABS_VOICE_ID


def is_configured() -> bool:
    return bool(ELEVENLABS_API_KEY)


def synthesize(text: str) -> Optional[bytes]:
    """Return MP3 audio bytes for the given text, or None if ElevenLabs isn't configured/failed."""
    if not is_configured() or not text.strip():
        return None
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": ELEVENLABS_MODEL_ID,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None
