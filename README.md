# Futurist-Studio
AI-powered automation platform for websites, chatbots, voice assistants, and business workflows

## FUTURIST OS

Ein persönliches KI-Betriebssystem: ein Executive Agent koordiniert sechs Fachagenten
(Developer, Design, Marketing, Research, Automation, Finance) über Chat, Sprache, Browser
und Terminal. Architektur, DB-Schema, API-Design und Entwicklungsplan stehen in
[`docs/architecture/FUTURIST_OS_ARCHITECTURE.md`](docs/architecture/FUTURIST_OS_ARCHITECTURE.md).

**Phase 0 (Fundament) ist implementiert:**

| Ordner | Inhalt |
|---|---|
| `apps/api/` | FastAPI-Backend: Auth (JWT, Register/Login/Refresh/Logout), Postgres+Alembic, Redis-Health-Check |
| `apps/web/` | React + TypeScript + Tailwind Dashboard: Dark/Anthrazit/Silber-Theme, Navigation, Login |
| `infra/` | Docker Compose (Postgres, Redis, API, Web) |

Setup: [`apps/api/README.md`](apps/api/README.md), [`apps/web/README.md`](apps/web/README.md),
[`infra/README.md`](infra/README.md).

## Jarvis

Ein persönlicher, sprachgesteuerter KI-Assistent (FastAPI + Claude + ElevenLabs +
Playwright), siehe [`jarvis/README.md`](jarvis/README.md) für Architektur und Setup.
