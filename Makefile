# FX Risk Platform — Makefile
# Run: make <command>

.PHONY: install dev test build stop clean

## Install all dependencies
install:
	cd backend && npm install
	cd frontend && npm install
	cd ml-engine && pip install -r requirements.txt

## Start all services locally (no Docker)
dev:
	@echo "Starting all services..."
	start /B cmd /C "cd backend && npm run dev"
	start /B cmd /C "cd ml-engine && uvicorn main:app --reload --port 8000"
	cd frontend && npm run dev

## Run all tests
test:
	cd backend && npm test
	cd ml-engine && python -m pytest tests/ -v

## Train ML models (run once)
train-ml:
	cd ml-engine && python ml/train_models.py

## Build Docker images
build:
	docker-compose build

## Start all services via Docker
up:
	docker-compose up -d

## Stop Docker services
stop:
	docker-compose down

## View logs
logs:
	docker-compose logs -f

## Clean up containers and volumes
clean:
	docker-compose down -v --remove-orphans
