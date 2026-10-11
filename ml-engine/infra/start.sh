#!/bin/bash
set -e

echo "============================================="
echo " FX Risk Engine - Starting API Server"
echo "============================================="
echo "Host: ${API_HOST:-0.0.0.0}"
echo "Port: ${API_PORT:-8000}"
echo "Log Level: ${LOG_LEVEL:-INFO}"
echo "============================================="

exec uvicorn api.main:app \
    --host "${API_HOST:-0.0.0.0}" \
    --port "${API_PORT:-8000}" \
    --log-level "${LOG_LEVEL:-info}" \
    --workers 2
