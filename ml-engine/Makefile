.PHONY: install dev run test lint clean docker-build docker-run

# Install dependencies
install:
	pip install -r requirements.txt

# Run API in development mode with auto-reload
dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run API in production mode
run:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Run the CLI analytics engine
cli:
	python -m fx_risk_engine.cli

# Run all tests
test:
	python -m pytest tests/ -v --tb=short

# Run tests with coverage
test-cov:
	python -m pytest tests/ -v --tb=short --cov=fx_risk_engine --cov=api --cov-report=term-missing

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

# Docker
docker-build:
	docker build -f infra/Dockerfile -t fx-risk-engine .

docker-run:
	docker run -p 8000:8000 --env-file .env fx-risk-engine

# Docker Compose
compose-up:
	docker-compose -f infra/docker-compose.yml up -d

compose-down:
	docker-compose -f infra/docker-compose.yml down
