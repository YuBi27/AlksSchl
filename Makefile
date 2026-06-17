.PHONY: up down build migrate seed test logs

COMPOSE = docker compose -f docker-compose.yml -f docker-compose.dev.yml

up: ## Start all services
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

build: ## Rebuild images
	$(COMPOSE) build

migrate: ## Run Alembic migrations
	$(COMPOSE) run --rm api alembic upgrade head

seed: ## Populate DB with test data
	$(COMPOSE) run --rm api python seed.py

test: ## Run API tests
	$(COMPOSE) run --rm api pytest tests/ -v

logs: ## Tail logs
	$(COMPOSE) logs -f
