from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.dependencies import get_current_user
from app.media.speech import synthesize_speech, tts_configured, transcribe_audio
from app.models.user import User
from app.schemas.voice import SpeakRequest, TranscriptionResponse

router = APIRouter(prefix="/voice", tags=["voice"])

_MAX_AUDIO_BYTES = 25 * 1024 * 1024


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(file: UploadFile, _: User = Depends(get_current_user)) -> TranscriptionResponse:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Keine Audiodatei erhalten.")
    if len(audio_bytes) > _MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audiodatei ist zu gross (max. 25 MB).")

    try:
        text = await transcribe_audio(audio_bytes, file.filename or "audio.webm")
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Transkription fehlgeschlagen: {exc}") from exc

    return TranscriptionResponse(text=text)


@router.post("/speak")
async def speak(payload: SpeakRequest, _: User = Depends(get_current_user)) -> Response:
    if not tts_configured():
        raise HTTPException(status_code=501, detail="Sprachausgabe ist nicht konfiguriert (ELEVENLABS_API_KEY fehlt).")
    try:
        audio_bytes = await synthesize_speech(payload.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Sprachausgabe fehlgeschlagen: {exc}") from exc
    return Response(content=audio_bytes, media_type="audio/mpeg")
