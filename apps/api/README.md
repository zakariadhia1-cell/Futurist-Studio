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

## Wissensdatenbank & Gedaechtnis (Phase 2)

Braucht die `vector`-Extension (Postgres): lokal `postgresql-16-pgvector` installieren
und einmalig `CREATE EXTENSION vector;` (macht die erste Phase-2-Migration automatisch,
sofern der DB-User dazu berechtigt ist - im Docker-Compose-Setup der Fall, lokal ggf.
als Superuser). Ohne `OPENAI_API_KEY` laeuft die Embeddings-Erzeugung ueber einen
deterministischen Bag-of-Words-Fallback (funktional, aber keine echte Semantik).

REST: `GET/POST /api/v1/knowledge/documents`, `GET/DELETE /api/v1/knowledge/documents/{id}`,
`POST /api/v1/knowledge/search`. Der Chat-WebSocket durchsucht bei jeder Nachricht
automatisch Dokumente und `memory_facts` und haengt relevante Treffer (Cosine-Distanz
< 0.9) an den System-Prompt an.

## Multi-Agent-Orchestrierung & Tools (Phase 3)

Drei Agenten (`executive`, `developer`, `research`) mit eigenen Tool-Sets (siehe
`scripts/seed.py`). Tool-Calling laeuft ueber `ModelProvider.chat_with_tools()`
(Anthropic und OpenAI unterstuetzen es nativ; Ollama noch nicht). Ein Agent mit Tools
durchlaeuft die Schleife in `app/orchestrator/runner.py::run_agent_turn` (max.
`MAX_TOOL_ITERATIONS` Runden) statt der einfachen Streaming-Antwort - dadurch verliert
er live Token-Streaming zugunsten von Tool-Nutzung; der finale Text wird stattdessen
wortweise ans Frontend "nachgestreamt".

Tools (`app/orchestrator/tools/`): `delegate_to_agent` (Executive delegiert an einen
Fachagenten), `create_task`/`prioritize_projects` (Projekte/Aufgaben), `read_memory`
(Wissensdatenbank-Suche als expliziter Tool-Aufruf), `read_file`/`write_file`/
`run_terminal_command` (Developer, sandboxed auf `WORKSPACES_DIR/<user_id>/` - siehe
den Sicherheitshinweis in `app/orchestrator/tools/sandbox.py`), `web_search`/`read_page`
(Research, DuckDuckGo + httpx, kein API-Key noetig).

Neue REST-Endpunkte: `GET/POST/PATCH/DELETE /api/v1/projects`, `.../tasks`.

## Browser- & Terminalsteuerung (Phase 4)

**Browser** (`app/live/browser_manager.py`): Playwright-Sessions **im API-Prozess**
statt in einem eigenen `browser-worker`-Container (Architektur-Dokument empfiehlt
Isolation in einem separaten Service - hier bewusst zugunsten eines schnell lauffaehigen
Features reduziert; Session-/Aktions-API ist bereits so geschnitten, dass sie sich spaeter
hinter eine Job-Queue in einen echten Worker verschieben laesst). Fuer lokale Tests ohne
`playwright install` in dieser Sandbox: `PLAYWRIGHT_EXECUTABLE_PATH` in `.env` auf einen
vorhandenen Chromium-Pfad setzen.

REST: `GET/POST /api/v1/browser/sessions`, `DELETE /api/v1/browser/sessions/{id}`.
WebSocket: `/ws/browser/{session_id}?token=...` — `{"type":"action","action":"navigate"
|"click"|"fill"|"go_back"|"screenshot","args":{...}}` rein, `screenshot`/`result`/`error`
raus (Screenshot als Base64-PNG nach jeder Aktion).

**Terminal** (`app/live/terminal_manager.py`): echtes PTY (`os.openpty`), kein reines
Pipe-Streaming — interaktive Programme funktionieren korrekt. Sandboxed auf
`WORKSPACES_DIR/<user_id>/`, gleicher Hinweis wie beim `run_terminal_command`-Tool:
Verzeichnis-Ebene, kein echtes OS-Sandboxing.

REST: `GET/POST /api/v1/terminal/sessions`, `DELETE /api/v1/terminal/sessions/{id}`.
WebSocket: `/ws/terminal/{session_id}?token=...` — `{"type":"input","data":"..."}` oder
`{"type":"resize","rows":...,"cols":...}` rein, `{"type":"output","data":"..."}` raus.

## Restliche Fachagenten (Phase 5)

Vier weitere Agenten (`design`, `marketing`, `finance`, `automation`), siehe
`scripts/seed.py` fuer Systemprompt und Tool-Zuordnung.

- **Design**: `generate_image` (OpenAI `dall-e-3`, nutzt `OPENAI_API_KEY`) - speichert
  Ergebnisse im Workspace unter `images/`.
- **Marketing**: `seo_analyze` (echte Heuristiken - Title-/Meta-Laenge, H1-Anzahl,
  fehlende Bild-Alt-Texte, Textumfang; kein externer SEO-Dienst noetig) + `web_search`.
- **Finance**: `calculate` (sicherer AST-basierter Ausdrucksauswerter, kein `eval()`),
  `generate_invoice_pdf`/`generate_report` (echte PDFs via `reportlab`, gespeichert unter
  `invoices/`/`reports/`).
- **Automation**: `list_n8n_workflows`/`trigger_n8n_workflow` (n8n-REST-API bzw.
  Webhook-Pfad, braucht `N8N_BASE_URL`/`N8N_API_KEY` - siehe `infra/docker-compose.yml`
  fuer den mitgelieferten n8n-Service), `call_api` (generischer HTTP-Aufruf mit
  SSRF-Schutz in `app/orchestrator/tools/ssrf_guard.py` - interne/private Netzwerkziele
  werden abgelehnt).

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
