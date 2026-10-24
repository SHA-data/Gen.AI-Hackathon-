.PHONY: help dev test migrate seed lint clean

help:
	@echo "Available commands:"
	@echo "  make dev      - Start FastAPI development server"
	@echo "  make test     - Run pytest test suite"
	@echo "  make migrate  - Run Alembic database migrations"
	@echo "  make seed     - Seed database with demo tenants and accounts"
	@echo "  make lint     - Run linter checks (ruff/black)"
	@echo "  make clean    - Remove cache and temporary files"

dev:
	uvicorn services.api.app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

migrate:
	alembic -c services/api/alembic.ini upgrade head

seed:
	python services/api/seed/seed_data.py

lint:
	ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
