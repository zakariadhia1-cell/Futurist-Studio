"""FastAPI server for Jarvis - the local brain/action hub between browser, Claude, ElevenLabs and tools."""
import base64
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jarvis.backend import actions, tts
from jarvis.backend.brain import think
from jarvis.backend.config import CORS_ORIGINS
from jarvis.backend.tasks import get_tasks
from jarvis.backend.weather import get_weather_summary

app = FastAPI(title="Jarvis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    text: str
    history: list[Message]
    action: str | None = None
    audio_base64: str | None = None


class TTSRequest(BaseModel):
    text: str


def _run_turn(user_message: str, history: list[Message]) -> ChatResponse:
    convo = [{"role": m.role, "content": m.content} for m in history]
    convo.append({"role": "user", "content": user_message})

    raw_reply = think(convo)
    parsed = actions.parse_reply(raw_reply)
    convo.append({"role": "assistant", "content": raw_reply})

    final_text = parsed.spoken_text
    if parsed.action:
        result = actions.execute_action(parsed.action, parsed.action_arg)
        convo.append({"role": "user", "content": f"Aktionsergebnis: {result}"})
        follow_up_raw = think(convo)
        follow_up = actions.parse_reply(follow_up_raw)
        convo.append({"role": "assistant", "content": follow_up_raw})
        final_text = follow_up.spoken_text or parsed.spoken_text

    audio_b64 = None
    audio_bytes = tts.synthesize(final_text)
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return ChatResponse(
        text=final_text,
        history=[Message(role=m["role"], content=m["content"]) for m in convo],
        action=parsed.action,
        audio_base64=audio_b64,
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message darf nicht leer sein")
    return _run_turn(req.message, req.history)


@app.post("/api/activate", response_model=ChatResponse)
def activate():
    weather = get_weather_summary()
    tasks = get_tasks()
    tasks_line = "; ".join(tasks) if tasks else "keine offenen Aufgaben"
    context_message = f"Kontext fuer diese Aktivierung - Wetter: {weather}. Aufgaben: {tasks_line}."
    history = [Message(role="user", content=context_message)]
    return _run_turn('Sir sagt: "Jarvis activate"', history)


@app.post("/api/tts")
def synthesize_speech(req: TTSRequest):
    audio_bytes = tts.synthesize(req.text)
    if audio_bytes is None:
        raise HTTPException(status_code=501, detail="ElevenLabs ist nicht konfiguriert (ELEVENLABS_API_KEY fehlt).")
    return Response(content=audio_bytes, media_type="audio/mpeg")


_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
