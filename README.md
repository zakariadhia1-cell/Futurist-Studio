# Futurist-Studio
AI-powered automation platform for websites, chatbots, voice assistants, and business workflows

## FUTURIST OS

Ein persönliches KI-Betriebssystem: ein Executive Agent koordiniert sechs Fachagenten
(Developer, Design, Marketing, Research, Automation, Finance) über Chat, Sprache, Browser
und Terminal. Architektur, DB-Schema, API-Design und Entwicklungsplan stehen in
[`docs/architecture/FUTURIST_OS_ARCHITECTURE.md`](docs/architecture/FUTURIST_OS_ARCHITECTURE.md).

**Phase 0-10 (Fundament, Core Chat, Wissensdatenbank, Multi-Agent-Orchestrierung, Browser-/Terminalsteuerung, alle 7 Fachagenten, Vision/OCR/Sprache, Dateien/Notizen, Plugin-System via MCP, Sicherheit & Haertung, Politur & Launch-Doku) sind implementiert - das komplette 11-Phasen-Projekt aus der Architektur bis auf Kalender/E-Mail (siehe unten):**

| Ordner | Inhalt |
|---|---|
| `apps/api/` | FastAPI-Backend: Auth (JWT) mit Audit-Logging und Rate-Limiting, RBAC, Verschluesselung at rest (Fernet), Postgres+Alembic, Redis, Model-Abstraction (OpenAI/Anthropic/Ollama) inkl. Tool-Calling und Vision, pgvector-Wissensdatenbank mit automatischer Kontext-Einbindung im Chat, alle 7 Agenten (Executive, Developer, Research, Design, Marketing, Finance, Automation) mit Tools und Delegation, Projekte/Aufgaben-API, Live-Browsersteuerung (Playwright) und Terminal-Sessions (echtes PTY), Bildgenerierung, PDF-Erstellung, SEO-Analyse, n8n-Integration, Vision/OCR, Sprachein-/-ausgabe (Whisper/ElevenLabs), Dateiverwaltung, Notizen, MCP-Client als Plugin-System, strukturiertes Logging |
| `apps/web/` | React + TypeScript + Tailwind Dashboard: Dark/Anthrazit/Silber-Theme, Navigation, Login, Chat-UI mit Streaming + Spracheingabe/-ausgabe, Wissensdatenbank-, Agenten-, Projekte-, Aufgaben-, Dateien-, Notizen-, Browser- (Live-Screenshot), Terminal-UI (xterm.js) und MCP-Server-Verwaltung in den Einstellungen |
| `infra/` | Docker Compose (Postgres mit pgvector, Redis, API, Web, n8n) + Backup-/Restore-Skripte |

Kalender-/E-Mail-Integration (letzter Teil von Phase 7) ist bewusst noch offen: sie braucht
Google-OAuth-Client-Credentials, die nur der Nutzer selbst in der Google Cloud Console
anlegen kann - siehe [`apps/api/README.md`](apps/api/README.md#kalender--e-mail-phase-7---offen).

Setup: [`apps/api/README.md`](apps/api/README.md), [`apps/web/README.md`](apps/web/README.md),
[`infra/README.md`](infra/README.md). Produktivbetrieb:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`docs/GO_LIVE_CHECKLIST.md`](docs/GO_LIVE_CHECKLIST.md).

## Jarvis

Ein persönlicher, sprachgesteuerter KI-Assistent (FastAPI + Claude + ElevenLabs +
Playwright), siehe [`jarvis/README.md`](jarvis/README.md) für Architektur und Setup.
