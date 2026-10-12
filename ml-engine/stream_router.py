"""
stream_router.py — Streaming Monte Carlo FastAPI Router
========================================================
Adds the /run_montecarlo_stream endpoint that:
  - Accepts exposure portfolio + simulation params
  - Runs the correlated streaming Monte Carlo
  - Streams NDJSON (newline-delimited JSON) chunks back to Node.js backend
  - Final line is the complete risk metrics object

Node.js backend consumes this stream and forwards chunks via Socket.io to React.
"""

import json
import logging
from typing import List, Optional, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

import config
from montecarlo_stream import run_correlated_monte_carlo
from data.live_rates import get_live_rates

logger = logging.getLogger("fx_risk_engine.stream_router")

router = APIRouter(tags=["Streaming Simulation"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ExposureItem(BaseModel):
    name: str = "Exposure"
    exp_type: str = Field(default="revenue", pattern="^(revenue|cost)$")
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "expType" in data and "exp_type" not in data:
                data["exp_type"] = data["expType"]
            if not data.get("name"):
                data["name"] = f"{data.get('currency', 'FX')}_{data.get('exp_type', 'exp')}"
        return data


class MonteCarloStreamRequest(BaseModel):
    exposures: List[ExposureItem]
    base_currency: str = "EUR"
    iterations: int = Field(default=5000, ge=100, le=50000)
    chunk_size: int = Field(default=500, ge=100, le=2000)
    seed: Optional[int] = None
    # Optional: caller can pass pre-fetched rates (Node.js passes live rates)
    fx_rates: Optional[dict] = None
    fx_volatility: Optional[dict] = None


class PnLRequest(BaseModel):
    exposures: List[ExposureItem]
    base_currency: str = "EUR"
    fx_rates: Optional[dict] = None


# ── Streaming Endpoint ────────────────────────────────────────────────────────

@router.post("/run_montecarlo_stream")
async def run_montecarlo_stream(request: MonteCarloStreamRequest):
    """
    Streams Monte Carlo simulation results as NDJSON.
    Each line is either:
      {"type": "chunk", "profits": [...], "progress": 0.35, "iteration": 1750}
      {"type": "complete", "mean_profit": ..., "var_95": ..., "risk_level": "MEDIUM", ...}
    """
    exposures = [e.model_dump() for e in request.exposures]

    # Use caller-provided rates or fetch live
    rates = request.fx_rates or get_live_rates(request.base_currency)
    volatility = request.fx_volatility or config.FX_VOLATILITY

    def generate():
        try:
            for event_type, payload in run_correlated_monte_carlo(
                exposures=exposures,
                base_fx_rates=rates,
                fx_volatility=volatility,
                base_currency=request.base_currency,
                iterations=request.iterations,
                seed=request.seed,
                chunk_size=request.chunk_size,
            ):
                line = json.dumps({"type": event_type, **payload}) + "\n"
                yield line
        except Exception as e:
            logger.error("Streaming Monte Carlo error: %s", e, exc_info=True)
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"},  # disable nginx buffering
    )


# ── Live PnL (used by what-if slider) ────────────────────────────────────────

@router.post("/run_pnl")
async def run_pnl(request: PnLRequest):
    """
    Fast deterministic P&L computation using provided or live rates.
    Called by Node.js backend for every slider drag event.
    """
    from montecarlo_stream import _compute_pnl

    rates = request.fx_rates or get_live_rates(request.base_currency)
    exposures = [e.model_dump() for e in request.exposures]

    profit = _compute_pnl(exposures, rates, request.base_currency)

    # Breakdown by exposure
    breakdown = []
    for exp in exposures:
        ccy = exp["currency"]
        rate = rates.get(ccy, 1.0) if ccy != request.base_currency else 1.0
        value_in_base = exp["amount"] / rate if rate != 0 else 0
        if exp.get("exp_type", "revenue") == "cost":
            value_in_base = -value_in_base
        breakdown.append({
            "name": exp["name"],
            "currency": ccy,
            "amount": exp["amount"],
            "value_in_base": round(value_in_base, 2),
            "rate_used": round(rate, 6),
        })

    total_revenue = sum(b["value_in_base"] for b in breakdown if b["value_in_base"] > 0)
    total_cost    = abs(sum(b["value_in_base"] for b in breakdown if b["value_in_base"] < 0))

    return {
        "base_currency": request.base_currency,
        "profit": round(profit, 2),
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "margin": round(profit / total_revenue, 4) if total_revenue > 0 else 0,
        "breakdown": breakdown,
        "rates_used": rates,
    }
