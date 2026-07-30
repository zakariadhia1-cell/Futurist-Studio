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
