.PHONY: up down logs ps clean run test install dev \
        init-db db-migrate db-downgrade db-revision \
        format lint check

# ────────────────────────────
# Docker Commands
# ────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

clean: down
	docker compose down -v --remove-orphans

# ────────────────────────────
# Application Commands
# ────────────────────────────

run:
	poetry run uvicorn github_analysis.main:app --reload

test:
	poetry run pytest

install:
	poetry install

dev: up run

# ────────────────────────────
# Database Commands (Alembic)
# ────────────────────────────

init-db:
	poetry add alembic
	poetry run alembic init migrations

db-migrate:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

db-revision:
	poetry run alembic revision --autogenerate -m "$(message)"

# ────────────────────────────
# Code Quality Commands
# ────────────────────────────

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run flake8 .
	poetry run mypy .

check: format lint test
