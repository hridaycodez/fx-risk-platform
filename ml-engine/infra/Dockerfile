# ── Build Stage ───────────────────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime Stage ─────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY fx_risk_engine/ ./fx_risk_engine/
COPY api/ ./api/
COPY ml/ ./ml/
COPY .env .env
COPY infra/start.sh ./start.sh

RUN chmod +x start.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["./start.sh"]
