.PHONY: up down logs ps clean run test install dev

# Docker commands
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

# Application commands (Use Poetry for running the app)
run:
	poetry run uvicorn github_analysis.main:app --reload

# Development commands (Use Poetry for testing)
test:
	poetry run pytest

# Install dependencies using Poetry
install:
	poetry install

# Combined commands (Run Docker and App together)
dev: up run

init-db:
	poetry add alembic
	poetry run alembic init migrations


db-migrate:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

db-revision:
	poetry run alembic revision --autogenerate -m "$(message)"