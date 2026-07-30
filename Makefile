.PHONY: up down logs migrate seed test-api

up:
	docker compose -f infra/docker-compose.yml --env-file infra/.env up --build

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

migrate:
	docker compose -f infra/docker-compose.yml exec api alembic upgrade head

seed:
	docker compose -f infra/docker-compose.yml exec api python scripts/seed.py

test-api:
	docker compose -f infra/docker-compose.yml exec api pytest
