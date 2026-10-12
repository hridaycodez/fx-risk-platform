"""
FX Risk Engine — API Application
==================================

FastAPI application with CORS, structured logging, custom exception
handlers, and router registration.

Run with:
    uvicorn api.main:app --reload --port 8000
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from fx_risk_engine.config.settings import get_settings
from api.routers import exposures, scenarios, analytics

# ── Logging Setup ─────────────────────────────────────────────────────

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("fx_risk_engine.api")


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("FX Risk Engine API starting up")
    logger.info("Base Currency: %s", settings.BASE_CURRENCY)
    logger.info("Monte Carlo Iterations: %d", settings.MC_ITERATIONS)
    logger.info("Debug Mode: %s", settings.DEBUG)
    logger.info("=" * 60)
    yield
    logger.info("FX Risk Engine API shutting down")


# ── App Factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="FX Risk Engine API",
    description=(
        "A modular foreign exchange risk simulation and analytics engine. "
        "Provides P&L computation, sensitivity analysis, Monte Carlo simulation, "
        "and statistical risk metrics (VaR, CVaR, downside probability)."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ───────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ───────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions as 422 responses."""
    logger.warning("ValueError: %s", str(exc))
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "status_code": 422,
        },
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """Handle KeyError exceptions as 400 responses."""
    logger.warning("KeyError: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Missing Key",
            "detail": f"Required key not found: {str(exc)}",
            "status_code": 400,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all exception handler."""
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
            "status_code": 500,
        },
    )


# ── Register Routers ─────────────────────────────────────────────────

app.include_router(exposures.router)
app.include_router(scenarios.router)
app.include_router(analytics.router)

# Streaming Monte Carlo + live PnL for the MERN frontend
from stream_router import router as stream_router
app.include_router(stream_router)


# ── Static Files ─────────────────────────────────────────────────────
import os
_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ── Root ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root(request: Request):
    """Return API info for API clients, or redirect browsers to dashboard UI."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="/static/index.html", status_code=302)
    return {
        "name": "FX Risk Engine API",
        "version": "0.1.0",
        "status": "online",
        "docs": "/docs",
    }


# ── CLI Entry Point ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
