# FUTURIST OS Web

React + TypeScript + Tailwind CSS Dashboard. Siehe
[`docs/architecture/FUTURIST_OS_ARCHITECTURE.md`](../../docs/architecture/FUTURIST_OS_ARCHITECTURE.md).

## Lokale Entwicklung

Voraussetzung: die API laeuft lokal auf `http://localhost:8000` (siehe `apps/api/README.md`).

```bash
npm install
npm run dev
```

Laeuft auf `http://localhost:5173`, `/api` wird per Vite-Proxy an die API weitergeleitet.

## Build

```bash
npm run build
```
