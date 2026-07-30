# Futurist-Studio
AI-powered automation platform for websites, chatbots, voice assistants, and business workflows

## FUTURIST OS

Ein persönliches KI-Betriebssystem: ein Executive Agent koordiniert sechs Fachagenten
(Developer, Design, Marketing, Research, Automation, Finance) über Chat, Sprache, Browser
und Terminal. Architektur, DB-Schema, API-Design und Entwicklungsplan stehen in
[`docs/architecture/FUTURIST_OS_ARCHITECTURE.md`](docs/architecture/FUTURIST_OS_ARCHITECTURE.md).

**Phase 0-3 (Fundament, Core Chat, Wissensdatenbank, Multi-Agent-Orchestrierung) sind implementiert:**

| Ordner | Inhalt |
|---|---|
| `apps/api/` | FastAPI-Backend: Auth (JWT), Postgres+Alembic, Redis, Model-Abstraction (OpenAI/Anthropic/Ollama) inkl. Tool-Calling, pgvector-Wissensdatenbank mit automatischer Kontext-Einbindung im Chat, 3 Agenten (Executive/Developer/Research) mit Tools und Delegation, Projekte/Aufgaben-API |
| `apps/web/` | React + TypeScript + Tailwind Dashboard: Dark/Anthrazit/Silber-Theme, Navigation, Login, Chat-UI mit Streaming, Wissensdatenbank-, Agenten-, Projekte- und Aufgaben-UI |
| `infra/` | Docker Compose (Postgres mit pgvector, Redis, API, Web) |

Setup: [`apps/api/README.md`](apps/api/README.md), [`apps/web/README.md`](apps/web/README.md),
[`infra/README.md`](infra/README.md).

## Jarvis

Ein persönlicher, sprachgesteuerter KI-Assistent (FastAPI + Claude + ElevenLabs +
Playwright), siehe [`jarvis/README.md`](jarvis/README.md) für Architektur und Setup.
