# FUTURIST OS - Deployment-Guide

Dieser Guide beschreibt, wie FUTURIST OS auf einem einzelnen Server (VPS oder
Root-Server) produktiv betrieben wird - fuer den in der Architektur vorgesehenen
Einsatz als persoenliches System eines einzelnen Admin-Nutzers, nicht als
Multi-Tenant-SaaS.

## 1. Voraussetzungen

- Ein Server mit Docker + Docker Compose (v2, `docker compose`, nicht das alte
  `docker-compose`).
- Eine Domain, die auf den Server zeigt (fuer TLS/HTTPS).
- API-Keys fuer mindestens einen Modell-Provider (Anthropic und/oder OpenAI) - ohne
  externe Provider funktioniert nur ein lokal via Ollama erreichbares Modell, und auch
  dann ohne Tool-Calling/Vision (siehe `apps/api/README.md`).

## 2. Repository & Konfiguration

```bash
git clone <repo-url> futurist-os && cd futurist-os
cp infra/.env.example infra/.env
cp apps/api/.env.example apps/api/.env
```

In `apps/api/.env` mindestens setzen (siehe die Go-Live-Checkliste fuer die vollstaendige
Liste):

- `JWT_SECRET_KEY` - `openssl rand -hex 32`
- `ENCRYPTION_KEY` - `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `ANTHROPIC_API_KEY` und/oder `OPENAI_API_KEY`
- `ENV=production`, `DEBUG=false`
- `CORS_ORIGINS` - exakt die eigene Domain, z.B. `["https://futuristos.example.com"]`
- Optional `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GOOGLE_REDIRECT_URI` fuer Kalender/
  E-Mail (siehe Abschnitt 2a)

### 2a. Google-OAuth-Credentials fuer Kalender/E-Mail (optional)

1. [console.cloud.google.com](https://console.cloud.google.com) - neues Projekt anlegen.
2. **APIs & Dienste > Bibliothek**: **Google Calendar API** und **Gmail API** aktivieren.
3. **APIs & Dienste > OAuth-Zustimmungsbildschirm**: Nutzertyp "Extern", App-Name/
   Support-E-Mail ausfuellen, Scopes `calendar`, `gmail.readonly`, `gmail.send`
   hinzufuegen. Bei "Testnutzer" die eigene E-Mail eintragen - fuer rein persoenlichen
   Gebrauch muss die App nie veroeffentlicht werden.
4. **APIs & Dienste > Anmeldedaten > + Anmeldedaten erstellen > OAuth-Client-ID**,
   Anwendungstyp "Webanwendung".
   - **Autorisierte Weiterleitungs-URIs**: exakt der Wert von `GOOGLE_REDIRECT_URI`
     (Standard lokal: `http://localhost:8000/api/v1/auth/google/callback`; produktiv:
     `https://<domain>/api/v1/auth/google/callback`) - muss auf's Zeichen genau
     uebereinstimmen, sonst schlaegt der Flow mit `redirect_uri_mismatch` fehl.
   - **Autorisierte JavaScript-Quellen**: nicht erforderlich (der Flow laeuft komplett
     serverseitig, das Frontend leitet nur per `window.location.href` weiter), kann leer
     bleiben.
5. Client-ID und Client-Secret in `apps/api/.env` als `GOOGLE_CLIENT_ID`/
   `GOOGLE_CLIENT_SECRET` eintragen. Verbindung danach in FUTURIST OS unter
   **Einstellungen > Google-Konto**.

## 3. Start

```bash
cd infra
docker compose --env-file .env up -d --build
```

Migrationen und Seed-Daten laufen automatisch beim Start des `api`-Containers. Der erste
`POST /api/v1/auth/register`-Aufruf (also die erste Registrierung ueber die Web-UI) wird
automatisch `admin` - das *ist* der Onboarding-Schritt, es gibt keinen separaten
Setup-Assistenten.

## 4. Reverse Proxy & TLS

Die Compose-Services binden direkt auf `8000` (API) und `5173` (Web) - fuer eine echte
Domain gehoert ein TLS-terminierender Reverse-Proxy davor. Beispiel mit
[Caddy](https://caddyserver.com/) (automatisches Let's-Encrypt-TLS, keine manuelle
Zertifikatspflege):

```
# /etc/caddy/Caddyfile
futuristos.example.com {
    reverse_proxy /api/* localhost:8000
    reverse_proxy /ws/* localhost:8000
    reverse_proxy localhost:5173
}
```

Wichtig: `/ws/*` muss explizit mitgeroutet werden (Chat/Browser/Terminal laufen ueber
WebSockets, nicht ueber `/api/*`). Caddy handhabt das WebSocket-Upgrade automatisch ohne
zusaetzliche Konfiguration.

Mit nginx stattdessen: `proxy_set_header Upgrade $http_upgrade;` und
`proxy_set_header Connection "upgrade";` auf dem `/ws/`-Location-Block nicht vergessen -
das ist die haeufigste Fehlerquelle bei WebSockets hinter nginx.

## 5. Backups

`infra/scripts/backup.sh` per Cron auf dem Host einplanen (siehe `infra/README.md`).
Backups landen in `infra/backups/` - dieses Verzeichnis regelmaessig auf ein separates
Ziel (Object Storage, ein zweiter Host, ...) kopieren; ein Backup, das nur auf demselben
Server liegt wie die Daten, die es sichert, schuetzt nicht vor einem Ausfall dieses
Servers.

## 6. Monitoring

- `GET /api/v1/health` fuer einen einfachen Liveness-/Readiness-Check (prueft Postgres
  und Redis).
- `SENTRY_DSN` in `apps/api/.env` setzen, um Exceptions an Sentry zu melden (optional,
  siehe `apps/api/README.md`).
- Logs sind strukturiertes JSON auf stdout (`docker compose logs -f api`) - direkt an
  einen Log-Aggregator (Loki, CloudWatch, ...) weiterleitbar.

## 7. Updates

```bash
git pull
docker compose --env-file .env up -d --build
```

Migrationen laufen automatisch beim Neustart des `api`-Containers. Vor einem Update mit
Schema-Aenderungen: `infra/scripts/backup.sh` ausfuehren.

Siehe auch [`GO_LIVE_CHECKLIST.md`](GO_LIVE_CHECKLIST.md) fuer die abschliessende
Pruefliste vor dem ersten produktiven Start.
