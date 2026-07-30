# FUTURIST OS - Infra

Docker Compose fuer den Phase-0-Stack: PostgreSQL, Redis, API, Web.

```bash
cp .env.example .env
cp ../apps/api/.env.example ../apps/api/.env   # JWT_SECRET_KEY anpassen!

make -C .. up      # oder: docker compose -f docker-compose.yml --env-file .env up --build
```

- API: `http://localhost:8000` (`/docs` fuer Swagger)
- Web: `http://localhost:5173`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

Migrationen und Seed-Daten laufen automatisch beim Start des `api`-Containers
(`docker-entrypoint.sh`).

## Backups (Phase 9)

`scripts/backup.sh` sichert Postgres (`pg_dump`, gzip) und Redis (`SAVE` + Kopie der
`dump.rdb`) aus dem laufenden Compose-Stack, jeweils mit Zeitstempel nach
`infra/backups/` (nicht versioniert). Fuer den Produktivbetrieb per Cron einplanen:

```bash
0 3 * * * cd /pfad/zu/futurist-os/infra && ./scripts/backup.sh >> /var/log/futuristos-backup.log 2>&1
```

`scripts/restore.sh <postgres-backup.sql.gz>` spielt einen Postgres-Dump zurueck (mit
Sicherheitsabfrage). Redis wird bewusst *nicht* automatisch zurueckgespielt - es ist
Cache-/Pub-Sub-Zustand, kein Datenbestand (siehe Architektur-Dokument, Abschnitt 1.3);
das Skript begruendet das im Kommentar.
