
# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------
BACKEND_DIR := backend
FRONTEND_DIR := frontend
PYTHON := python
NPM := npm
DC := docker compose

# =============================================================================
# LIFECYCLE
# =============================================================================
.PHONY: dev stop restart clean
dev:
	$(DC) up --build

dev-detached:
	$(DC) up --build -d

watch:
	$(DC) watch

stop:
	$(DC) down

restart: stop dev

clean:
	$(DC) down -v
	rm -rf $(FRONTEND_DIR)/node_modules
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} +
	find $(BACKEND_DIR) -type f -name "*.pyc" -delete

# =============================================================================
# BACKEND
# =============================================================================
.PHONY: backend-dev backend-migrate backend-createsuperuser backend-test
backend-dev:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py runserver

backend-migrate:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py makemigrations
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate

backend-createsuperuser:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py createsuperuser

backend-test:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py test

.PHONY: docker-backend-dev docker-backend-migrate backend-shell
docker-backend-dev:
	$(DC) up -d backend

docker-backend-migrate:
	$(DC) exec backend $(PYTHON) manage.py makemigrations
	$(DC) exec backend $(PYTHON) manage.py migrate

docker-backend-test:
	$(DC) exec backend pytest api/tests/auth/test_views.py -v 

docker-backend-test-all:
	$(DC) exec backend pytest --reuse-db

backend-shell:
	$(DC) exec backend $(PYTHON) manage.py shell

# =============================================================================
# FRONTEND
# =============================================================================
.PHONY: frontend-install frontend-dev frontend-test
frontend-install:
	cd $(FRONTEND_DIR) && $(NPM) install

frontend-dev:
	cd $(FRONTEND_DIR) && $(NPM) run dev

frontend-test:
	cd $(FRONTEND_DIR) && $(NPM) run test

docker-frontend-dev:
	$(DC) up -d frontend

lint-fe:
	$(DC) exec frontend npm run lint

format-fe:
	$(DC) exec frontend npm run format

lint-be:
	$(DC) exec backend pre-commit run --all-files

# =============================================================================
# DATABASE
# =============================================================================
.PHONY: db-shell db-backup db-restore db-down db-up
db-shell:
	$(DC) exec postgres psql -U postgres -d docappoint

db-backup:
	$(DC) exec postgres pg_dump -U postgres docappoint > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	$(DC) exec -T db dropdb -U postgres --if-exists docappoint
	$(DC) exec -T db createdb -U postgres docappoint
	$(DC) exec -T db psql -U postgres docappoint < $(file)

db-down:
	$(DC) down -v

db-up:
	$(DC) up -d postgres

# =============================================================================
# MISC / UTILITIES
# ==============================================================================
.PHONY: docker-build docker-logs status
docker-build:
	$(DC) build

docker-logs:
	$(DC) logs -f

docker-status:
	$(DC) ps
