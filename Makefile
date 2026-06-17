.PHONY: up down build migrate seed test logs

up: ## Start all services
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down: ## Stop all services
	docker compose down

build: ## Rebuild images
	docker compose build

migrate: ## Run Alembic migrations
	docker compose run --rm api alembic upgrade head

seed: ## Populate DB with test data
	docker compose run --rm api python seed.py

test: ## Run API tests
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm api pytest tests/ -v

logs: ## Tail logs
	docker compose logs -f
