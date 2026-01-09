.PHONY: help setup up down logs clean test frontend backend worker beat

help:
	@echo "TestIt - Ephemeral Container Build System"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup      - Run setup validation"
	@echo "  make up         - Start all services with Docker Compose"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs from all services"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make test       - Run API tests"
	@echo "  make frontend   - Start frontend development server"
	@echo "  make backend    - Start backend development server"
	@echo "  make worker     - Start Celery worker"
	@echo "  make beat       - Start Celery beat"

setup:
	@./setup.sh

up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

test:
	@./test_api.sh

frontend:
	cd frontend && npm install && npm start

backend:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A app.celery_app worker --loglevel=info

beat:
	celery -A app.celery_app beat --loglevel=info
