.PHONY: help up down build logs shell-api shell-db migrate seed restart clean

help:
	@echo ""
	@echo "  BioTime Open — Dev Commands"
	@echo ""
	@echo "  make up          Start all services"
	@echo "  make down        Stop all services"
	@echo "  make build       Rebuild all images"
	@echo "  make logs        Tail all logs"
	@echo "  make migrate     Run DB migrations"
	@echo "  make seed        Seed initial data (admin user, device models)"
	@echo "  make shell-api   Open shell in API container"
	@echo "  make shell-db    Open psql in DB container"
	@echo "  make restart     Restart API + worker"
	@echo "  make clean       Remove all containers + volumes (DESTRUCTIVE)"
	@echo ""

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python manage.py seed

shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec db psql -U biotime -d biotime

restart:
	docker compose restart api worker beat

clean:
	@echo "WARNING: This will delete all data. Press Ctrl+C to cancel."
	@sleep 5
	docker compose down -v --remove-orphans

test:
	docker compose exec api pytest tests/ -v

lint:
	docker compose exec api ruff check .
	docker compose exec api mypy .
