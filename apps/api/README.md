# FUTURIST OS API

FastAPI-Backend. Siehe [`docs/architecture/FUTURIST_OS_ARCHITECTURE.md`](../../docs/architecture/FUTURIST_OS_ARCHITECTURE.md)
fuer die Gesamtarchitektur.

## Lokale Entwicklung (ohne Docker)

Voraussetzung: PostgreSQL 16 und Redis laufen lokal.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env   # anpassen, insb. JWT_SECRET_KEY

createuser futurist --pwprompt   # Passwort: futurist (oder .env anpassen)
createdb futurist_os -O futurist

alembic upgrade head
PYTHONPATH=. python scripts/seed.py   # legt Rollen 'admin'/'member' an

PYTHONPATH=. uvicorn app.main:app --reload
```

API laeuft dann auf `http://localhost:8000`, Swagger-Docs unter `/docs`.

Der erste registrierte Nutzer (`POST /api/v1/auth/register`) wird automatisch `admin`,
alle weiteren `member`.

## Chat (Phase 1)

`seed.py` legt drei `model_configs` (Anthropic, OpenAI, Ollama) und den `executive`-Agent
an. Ohne echte API-Keys in `.env` schlagen Anthropic/OpenAI-Aufrufe fehl (der
WebSocket-Handler faengt das pro Nachricht ab und schickt `{"type": "error"}"`, die
Verbindung bleibt offen) - fuer lokale Entwicklung ohne Keys entweder `OLLAMA_BASE_URL`
auf einen laufenden Ollama-Server zeigen lassen, oder `ANTHROPIC_API_KEY` setzen.

REST: `GET /api/v1/agents`, `GET/POST /api/v1/conversations`,
`GET /api/v1/conversations/{id}/messages`.
WebSocket: `/ws/chat/{conversation_id}?token=<access_token>` (Envelope:
`{"type": "user_message", "content": "..."}` rein, `token`/`done`/`error` raus).

## Tests

```bash
createdb futurist_os_test -O futurist
PYTHONPATH=. pytest
```

## Migrationen

```bash
alembic revision --autogenerate -m "beschreibung"
alembic upgrade head
```
