# =============================================================================
# VARIABLES
# =============================================================================
DC := docker compose
BACKEND_DIR := backend
FRONTEND_DIR := frontend
IS_CI := $(if $(CI),true,)

# =============================================================================
# DEVELOPMENT
# =============================================================================
.PHONY: dev dev-down dev-clean dev-restart

## Start development environment
dev:
	$(DC) up --build

## Start development in detached mode
dev-detached:
	$(DC) up --build -d

## Stop development environment
dev-down:
	$(DC) down

## Clean development environment
dev-clean:
	$(DC) down -v
	rm -rf $(FRONTEND_DIR)/node_modules

## Restart development environment
dev-restart: dev-down dev

## Watch for changes
dev-watch:
	$(DC) watch

# =============================================================================
# SERVICE MANAGEMENT
# =============================================================================
.PHONY: services-build services-logs services-status

## Build all services
services-build:
	$(DC) build

## Follow service logs
services-logs:
	$(DC) logs -f

## Show service status
services-status:
	$(DC) ps

# =============================================================================
# BACKEND
# =============================================================================
.PHONY: backend backend-migrate backend-shell backend-createsuperuser backend-test

## Start backend service
backend:
	$(DC) up -d backend

## Run migrations
backend-migrate:
	$(DC) exec backend python manage.py makemigrations
	$(DC) exec backend python manage.py migrate

## Open Django shell
backend-shell:
	$(DC) exec backend python manage.py shell

## Create superuser
backend-createsuperuser:
	$(DC) exec backend python manage.py createsuperuser

## Run backend tests
backend-test:
	$(DC) exec backend pytest --reuse-db

## Run specific test file
backend-test-file:
	$(DC) exec backend pytest $(FILE) -v

# =============================================================================
# FRONTEND
# =============================================================================
.PHONY: frontend

## Start frontend service
frontend:
	$(DC) up -d frontend

# =============================================================================
# DATABASE
# =============================================================================
.PHONY: database database-shell database-backup

## Start database service
database:
	$(DC) up -d postgres

## Connect to database shell
database-shell:
	$(DC) exec postgres psql -U postgres -d docappoint

## Backup database
database-backup:
	mkdir -p ./backup
	$(DC) exec postgres pg_dump -U postgres docappoint > ./backup/backup_$(shell date +%Y%m%d_%H%M%S).sql

clean-backups:
	rm -f ./backup/*.sql

## Restore database from file
database-restore:
	$(DC) exec -T postgres dropdb -U postgres --if-exists docappoint
	$(DC) exec -T postgres createdb -U postgres docappoint
	$(DC) exec -T postgres psql -U postgres docappoint < $(FILE)

# =============================================================================
# CODE QUALITY 
# =============================================================================
.PHONY: lint format lint-be lint-fe format-be format-fe

## Run all linting
lint: lint-be lint-fe

## Run all formatting
format: format-be format-fe

## Lint backend
lint-be:
	$(DC) exec backend pre-commit run --all-files

## Lint frontend
lint-fe:
	$(DC) exec frontend npm run lint

## Format frontend
format-fe:
	$(DC) exec frontend npm run format

## Format backend
format-be:
	$(DC) exec backend pre-commit run --all-files

# =============================================================================
# CI/CD COMMANDS
# =============================================================================
.PHONY: ci ci-fe ci-be

## Run full CI suite locally (for debugging CI issues)
ci: ci-fe ci-be

## Frontend CI suite
ci-fe: ci-fe-lint ci-fe-type-check ci-fe-test

ci-fe-lint:
	cd $(FRONTEND_DIR) && npm run lint

ci-fe-type-check:
	cd $(FRONTEND_DIR) && npm run type-check

ci-fe-test-file:
	$(DC) exec frontend npm run test -- $(FILE)

ci-fe-test:
	cd $(FRONTEND_DIR) && npm run test:run
ifneq ($(IS_CI),true)
	cd $(FRONTEND_DIR) && npm run test:coverage
endif

ci-fe-test-run-docker:
	docker run --rm \
		-e CI=true \
		$(shell echo $(REGISTRY)/$(IMAGE_NAME)-frontend:$(TAG) | tr '[:upper:]' '[:lower:]') \
		npm run test:run -- --watchAll=false

ci-fe-test-coverage-docker:
	docker run --rm \
		-e CI=true \
		$(shell echo $(REGISTRY)/$(IMAGE_NAME)-frontend:$(TAG) | tr '[:upper:]' '[:lower:]') \
		npm run test:coverage -- --watchAll=false

ci-fe-test-docker: ci-fe-test-run-docker
	@if [ "$(IS_CI)" != "true" ]; then \
		$(MAKE) ci-fe-test-coverage-docker; \
	fi

## Backend CI suite
ci-be: ci-be-lint ci-be-type-check ci-be-migrations-check ci-be-test

ci-be-lint:
	cd $(BACKEND_DIR) && poetry run ruff check .
	cd $(BACKEND_DIR) && poetry run ruff format --check .

ci-be-type-check:
	cd $(BACKEND_DIR) && poetry run mypy api

ci-be-migrations-check:
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=api.settings.development poetry run python manage.py makemigrations --check --dry-run

ci-be-migrations-check-docker:
	docker run --rm \
		--network host \
		-e DATABASE_URL=$$DATABASE_URL \
		-e DJANGO_SECRET_KEY=$$DJANGO_SECRET_KEY \
		-e DJANGO_SETTINGS_MODULE=$$DJANGO_SETTINGS_MODULE \
		$(shell echo $(REGISTRY)/$(IMAGE_NAME)-backend:$(TAG) | tr '[:upper:]' '[:lower:]') \
		python manage.py makemigrations --check --dry-run

ci-be-test:
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=api.settings.development poetry run pytest --cov=api --cov-report=xml --cov-report=html

## Database setup for CI
ci-db-setup:
	cd $(FRONTEND_DIR) && npm ci
	cd $(BACKEND_DIR) && poetry install --no-interaction --no-root --no-ansi
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=api.settings.development poetry run python manage.py makemigrations api --noinput
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=api.settings.development poetry run python manage.py migrate api
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=api.settings.development poetry run python manage.py migrate

ci-be-test-docker:
	docker run --rm \
		--network host \
		-e DATABASE_URL=$$DATABASE_URL \
		-e REDIS_URL=$$REDIS_URL \
		-e DJANGO_SECRET_KEY=$$DJANGO_SECRET_KEY \
		-e DJANGO_SETTINGS_MODULE=$$DJANGO_SETTINGS_MODULE \
		$(shell echo $(REGISTRY)/$(IMAGE_NAME)-backend:$(TAG) | tr '[:upper:]' '[:lower:]') \
		pytest

## Run both container tests
ci-test-docker: ci-fe-test-docker ci-be-test-docker
	@echo "✅ All container tests passed"

# =============================================================================
# HELP
# =============================================================================
.PHONY: help

## Display this help message
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start all services"
	@echo "  make dev-down         Stop all services"
	@echo "  make dev-clean        Stop and remove volumes"
	@echo "  make dev-restart      Restart all services"
	@echo "  make dev-watch        Watch for file changes"
	@echo ""
	@echo "Individual Services:"
	@echo "  make backend          Start backend only"
	@echo "  make frontend         Start frontend only"
	@echo "  make database         Start database only"
	@echo ""
	@echo "Backend Operations:"
	@echo "  make backend-migrate          Run migrations"
	@echo "  make backend-shell            Open Django shell"
	@echo "  make backend-createsuperuser  Create admin user"
	@echo "  make backend-test             Run all tests"
	@echo "  make backend-test-file FILE=path  Run specific test file"
	@echo ""
	@echo "Database Operations:"
	@echo "  make database-shell           Connect to PostgreSQL"
	@echo "  make database-backup          Create database backup"
	@echo "  make database-restore FILE=   Restore from backup"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              Run all linting"
	@echo "  make format            Run all formatting"
	@echo ""
	@echo "CI/CD (Local Debugging):"
	@echo "  make ci                Run full CI suite locally"
	@echo "  make ci-be             Run backend CI checks"
	@echo "  make ci-fe             Run frontend CI checks"
	@echo ""
	@echo "Utilities:"
	@echo "  make services-status   Show container status"
	@echo "  make services-logs     Follow service logs"
	@echo "  make services-build    Rebuild all images"