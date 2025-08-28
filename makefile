# Variables
BACKEND_DIR = backend
FRONTEND_DIR = frontend
PYTHON = python
PIP = pip
NPM = npm

dev:
	docker compose up --build

stop:
	docker compose down

restart: stop dev

clean:
	docker compose down -v
	rm -rf $(FRONTEND_DIR)/node_modules
	rm -rf $(BACKEND_DIR)/__pycache__
	rm -rf $(BACKEND_DIR)/*.pyc

# General command
docker-down:
	docker compose down

docker-down-backup:
	docker compose exec db pg_dump -U postgres docappoint > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	docker compose down

docker-up-detached:
	docker compose up -d

docker-up:
	docker compose up

# Backend commands
docker-backend-dev:
	docker compose up -d backend

backend-dev:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py runserver

backend-migrate:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py makemigrations
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate

docker-backend-migrate:
	docker compose exec backend python manage.py makemigrations
	docker compose exec backend python manage.py migrate

backend-createsuperuser:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py createsuperuser

backend-test:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py test

backend-shell:
	docker compose exec backend python manage.py shell

# Frontend commands
docker-frontend-dev:
	docker compose up frontend

frontend-install:
	cd $(FRONTEND_DIR) && $(NPM) install

frontend-dev:
	cd $(FRONTEND_DIR) && $(NPM) run dev

frontend-test:
	cd $(FRONTEND_DIR) && $(NPM) run test

# Database commands
db-restore:
	docker compose exec db dropdb -U postgres --if-exists docappoint
	docker compose exec db createdb -U postgres docappoint
# 	cat $(file) | docker compose exec -T db psql -U postgres docappoint
	docker compose exec -T db psql -U postgres docappoint < $(file)

db-down:
	docker compose down -v

db-up:
	docker compose up -d db

db-shell:
	docker compose exec db psql -U postgres -d docappoint

db-backup:
	docker compose exec db pg_dump -U postgres docappoint > backup_$(shell date +%Y%m%d_%H%M%S).sql

docker-build:
	docker compose build

# Utility Commands
status:
	docker compose ps

# Database migration targets
db-makemigrations:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py makemigrations

db-migrate:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate