# FUTURIST OS - Go-Live-Checkliste

Vor dem ersten produktiven Start pruefen. Siehe [`DEPLOYMENT.md`](DEPLOYMENT.md) fuer den
vollstaendigen Deployment-Ablauf.

## Umgebungsvariablen (`apps/api/.env`)

- [ ] `JWT_SECRET_KEY` - eigener Wert, nicht der Platzhalter aus `.env.example`
      (`openssl rand -hex 32`)
- [ ] `ENCRYPTION_KEY` - gesetzt (`Fernet.generate_key()`), sonst werden MCP-Server-
      Secrets im Klartext gespeichert
- [ ] `ENV=production`, `DEBUG=false`
- [ ] `CORS_ORIGINS` - exakt die eigene(n) Domain(s), nicht `localhost`
- [ ] `DATABASE_URL`/`REDIS_URL` - zeigen auf die Produktions-Container/-Instanzen
- [ ] Mindestens ein Modell-Provider-Key gesetzt (`ANTHROPIC_API_KEY` und/oder
      `OPENAI_API_KEY`) - ohne beide funktioniert nur ein lokal erreichbares
      Ollama-Modell, ohne Tool-Calling/Vision
- [ ] Optionale Keys nach Bedarf: `ELEVENLABS_API_KEY` (Sprachausgabe),
      `N8N_API_KEY`/`N8N_BASE_URL` (Automation Agent), `SENTRY_DSN` (Fehler-Tracking)

## Infrastruktur

- [ ] Reverse Proxy mit TLS terminiert Traffic vor der API (siehe `DEPLOYMENT.md`
      Abschnitt 4) - insbesondere `/ws/*` fuer WebSockets korrekt weitergeleitet
- [ ] `infra/scripts/backup.sh` per Cron eingeplant, mindestens taeglich
- [ ] `infra/scripts/restore.sh` einmal gegen einen echten Test-Dump ausprobiert, *bevor*
      er im Ernstfall gebraucht wird
- [ ] Backups landen (auch) ausserhalb des Produktionsservers

## Nach dem ersten Start

- [ ] `GET /api/v1/health` liefert `{"status": "ok", "database": true, "redis": true}`
- [ ] Erste Registrierung ueber die Web-UI durchgefuehrt (wird automatisch `admin` -
      das ist der komplette Onboarding-Schritt, siehe `DEPLOYMENT.md`)
- [ ] `GET /api/v1/audit-logs` als Admin abrufbar (bestaetigt RBAC + Audit-Logging)
- [ ] Ein Chat mit dem Executive Agent erfolgreich getestet (bestaetigt, dass der
      konfigurierte Modell-Provider erreichbar ist)

## Bewusst nicht Teil dieser Checkliste

- **Lasttests**: siehe `apps/api/README.md`, Abschnitt "Sicherheit & Haertung" - ohne
  ein konkretes, reales Nutzungsprofil wuerde eine Kennzahl nichts aussagen. Nachholen,
  sobald ein solches Profil existiert.
- **Multi-Tenant-Haertung** (Rate-Limiting pro Nutzer statt IP, vollstaendige
  RBAC-Matrix pro Ressourcentyp, echtes OS-Sandboxing fuer Terminal/Browser): dieses
  System ist fuer einen einzelnen vertrauenswuerdigen Admin-Nutzer konzipiert (siehe
  Architektur-Dokument, Annahme in Abschnitt 0) - vor jeder Oeffnung fuer mehrere
  gegenseitig nicht vertrauende Nutzer waere das ein eigenes Projekt, kein Checklisten-
  Punkt.
