#!/usr/bin/env bash
# ==============================================================================
# FX Risk Platform - EC2 Container Launch Script
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=================================================="
echo "🚀 Deploying FX Risk Platform on EC2..."
echo "=================================================="

# Check if .env exists in backend
if [ ! -f backend/.env ]; then
    echo "⚠️ backend/.env not found! Creating from .env.example..."
    cp backend/.env.example backend/.env
fi

# Build and start containers in detached mode
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker compose -f docker-compose.prod.yml up -d --build

echo "=================================================="
echo "📊 Checking Container Status..."
echo "=================================================="
sleep 5
docker compose -f docker-compose.prod.yml ps

echo "=================================================="
echo "✅ Deployment Finished!"
echo "Node.js Backend & API:   http://localhost:4000 (and port 80)"
echo "Python ML Engine:        http://localhost:8000"
echo "Health check:            http://localhost:4000/health"
echo "=================================================="
