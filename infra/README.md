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
