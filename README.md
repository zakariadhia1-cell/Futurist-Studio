# Futurist-Studio

Next-generation personal AI operating system with autonomous agents, voice interaction, computer control, browser automation, long-term memory, and intelligent workflow management.

## FUTURIST OS

Ein persönliches KI-Betriebssystem: ein Executive Agent koordiniert sechs Fachagenten
(Developer, Design, Marketing, Research, Automation, Finance) über Chat, Sprache, Browser
und Terminal. Architektur, DB-Schema, API-Design und Entwicklungsplan stehen in
[`docs/architecture/FUTURIST_OS_ARCHITECTURE.md`](docs/architecture/FUTURIST_OS_ARCHITECTURE.md).

**Alle 11 Phasen aus der Architektur sind implementiert** (Fundament, Core Chat,
Wissensdatenbank, Multi-Agent-Orchestrierung, Browser-/Terminalsteuerung, alle 7
Fachagenten, Vision/OCR/Sprache, Dateien/Notizen/Kalender/E-Mail, Plugin-System via MCP,
Sicherheit & Haertung, Politur & Launch-Doku), inklusive eines neuen visuellen
Kontrollzentrums (`/os` im Web-Dashboard: Systemuebersicht, Agenten-Steuerung,
Aufgaben/Projekte, Shopify/Gastro-Uebersichten, Chat, Automationen, Monitoring,
Benachrichtigungen, Analysen, Einstellungen):

| Ordner | Inhalt |
|---|---|
| `apps/api/` | FastAPI-Backend: Auth (JWT) mit Audit-Logging und Rate-Limiting, RBAC, Verschluesselung at rest (Fernet), Postgres+Alembic, Redis, Model-Abstraction (OpenAI/Anthropic/Ollama) inkl. Tool-Calling und Vision, pgvector-Wissensdatenbank mit automatischer Kontext-Einbindung im Chat, alle 7 Agenten (Executive, Developer, Research, Design, Marketing, Finance, Automation) mit Tools und Delegation, Projekte/Aufgaben-API, Live-Browsersteuerung (Playwright) und Terminal-Sessions (echtes PTY), Bildgenerierung, PDF-Erstellung, SEO-Analyse, n8n-Integration, Vision/OCR, Sprachein-/-ausgabe (Whisper/ElevenLabs), Dateiverwaltung, Notizen, Google-Kalender/-Gmail, MCP-Client als Plugin-System, strukturiertes Logging, aggregierter Dashboard-Summary-Endpoint |
| `apps/web/` | React + TypeScript + Tailwind Dashboard: Dark/Anthrazit/Silber-Theme, Navigation, Login, Chat-UI mit Streaming + Spracheingabe/-ausgabe, Wissensdatenbank-, Agenten-, Projekte-, Aufgaben-, Dateien-, Notizen-, Browser- (Live-Screenshot), Terminal-UI (xterm.js) sowie MCP-Server- und Google-Konto-Verwaltung in den Einstellungen; zusaetzlich ein eigenstaendiges Neon-Glassmorphism-Kontrollzentrum unter `/os` |
| `infra/` | Docker Compose (Postgres mit pgvector, Redis, API, Web, n8n) + Backup-/Restore-Skripte |

Setup: [`apps/api/README.md`](apps/api/README.md), [`apps/web/README.md`](apps/web/README.md),
[`infra/README.md`](infra/README.md). Produktivbetrieb:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`docs/GO_LIVE_CHECKLIST.md`](docs/GO_LIVE_CHECKLIST.md).

## Jarvis

Ein persönlicher, sprachgesteuerter KI-Assistent (FastAPI + Claude + ElevenLabs +
Playwright), siehe [`jarvis/README.md`](jarvis/README.md) für Architektur und Setup.
