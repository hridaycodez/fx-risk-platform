"""
Analytics Router
================

Core computation endpoints: P&L, Sensitivity, Monte Carlo.
Also includes the health check endpoint.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.request_models import (
    RunPnLRequest,
    RunSensitivityRequest,
    RunMonteCarloRequest,
    PnLResponse,
    SensitivityResponse,
    MonteCarloResponse,
    HealthResponse,
)
from api.dependencies.config import get_store, get_app_settings
from api.services.scenario_service import SessionStore
from fx_risk_engine.config.settings import Settings
from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.analytics.pnl import PnLEngine, compute_pnl
from fx_risk_engine.analytics.sensitivity import (
    run_sensitivity_analysis,
    compute_sensitivity_summary,
)
from fx_risk_engine.analytics.risk_metrics import compute_risk_metrics
from fx_risk_engine.simulation.monte_carlo import run_monte_carlo
import fx_risk_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analytics"])


def _resolve_exposures(request, store: SessionStore):
    """Helper to resolve exposures from profile_id or inline data."""
    if request.profile_id:
        profile = store.get_profile(request.profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{request.profile_id}' not found.",
            )
        return profile.exposures
    elif request.exposures:
        return [
            Exposure(
                name=e.name,
                exp_type=e.exp_type,
                amount=e.amount,
                currency=e.currency,
            )
            for e in request.exposures
        ]
    else:
        raise HTTPException(
            status_code=422,
            detail="Either profile_id or exposures must be provided.",
        )


# ── Health Check ──────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
    description="Returns API health status, version, and engine readiness.",
)
def health_check() -> HealthResponse:
    """Basic system health check."""
    return HealthResponse(
        status="healthy",
        version=fx_risk_engine.__version__,
        engine_status="operational",
    )


# ── P&L ──────────────────────────────────────────────────────────────

@router.post(
    "/run_pnl",
    response_model=PnLResponse,
    summary="Run deterministic P&L",
    description="Compute profit & loss under base or stressed FX rates.",
)
def run_pnl(
    request: RunPnLRequest,
    store: SessionStore = Depends(get_store),
    settings: Settings = Depends(get_app_settings),
) -> PnLResponse:
    """Run deterministic scenario-based P&L computation."""
    try:
        exposures = _resolve_exposures(request, store)
        fx_rates = request.fx_rates or settings.BASE_FX_RATES
        base_currency = request.base_currency or settings.BASE_CURRENCY

        # Optionally apply a named scenario
        if request.scenario_name:
            scenario = store.get_scenario(request.scenario_name)
            if not scenario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Scenario '{request.scenario_name}' not found.",
                )
            fx_rates = scenario.apply_shock(fx_rates)

        engine = PnLEngine(exposures, fx_rates, base_currency)
        result = engine.compute()

        logger.info(
            "P&L computed: profit=%.2f %s", result["profit"], base_currency
        )

        return PnLResponse(
            total_revenue=result["total_revenue"],
            total_cost=result["total_cost"],
            profit=result["profit"],
            margin=result["margin"],
            base_currency=base_currency,
            breakdown=result["breakdown"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )


# ── Sensitivity ───────────────────────────────────────────────────────

@router.post(
    "/run_sensitivity",
    response_model=SensitivityResponse,
    summary="Run sensitivity analysis",
    description="Sweep a target currency across a shock range, returning profit curve data.",
)
def run_sensitivity(
    request: RunSensitivityRequest,
    store: SessionStore = Depends(get_store),
    settings: Settings = Depends(get_app_settings),
) -> SensitivityResponse:
    """Run single-currency sensitivity analysis."""
    try:
        exposures = _resolve_exposures(request, store)
        fx_rates = request.fx_rates or settings.BASE_FX_RATES
        base_currency = request.base_currency or settings.BASE_CURRENCY

        results = run_sensitivity_analysis(
            exposures=exposures,
            base_fx_rates=fx_rates,
            target_currency=request.target_currency,
            base_currency=base_currency,
            shock_range=request.shock_range,
        )

        summary = compute_sensitivity_summary(results)

        logger.info(
            "Sensitivity analysis for %s: %d data points",
            request.target_currency,
            len(results),
        )

        return SensitivityResponse(
            target_currency=request.target_currency,
            base_currency=base_currency,
            results=results,
            summary=summary,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )


# ── Monte Carlo ───────────────────────────────────────────────────────

@router.post(
    "/run_montecarlo",
    response_model=MonteCarloResponse,
    summary="Run Monte Carlo simulation",
    description="Simulates profit distribution under random FX shocks. Returns VaR, CVaR, and risk metrics.",
)
def run_montecarlo(
    request: RunMonteCarloRequest,
    store: SessionStore = Depends(get_store),
    settings: Settings = Depends(get_app_settings),
) -> MonteCarloResponse:
    """Run Monte Carlo simulation and return risk metrics."""
    try:
        exposures = _resolve_exposures(request, store)
        fx_rates = request.fx_rates or settings.BASE_FX_RATES
        base_currency = request.base_currency or settings.BASE_CURRENCY
        volatilities = request.volatilities or settings.FX_VOLATILITY

        # Run simulation
        profit_distribution = run_monte_carlo(
            exposures=exposures,
            base_fx_rates=fx_rates,
            volatilities=volatilities,
            base_currency=base_currency,
            iterations=request.iterations,
            seed=request.seed,
        )

        # Compute base case profit for risk metrics
        base_result = compute_pnl(exposures, fx_rates, base_currency)
        base_profit = base_result["profit"]

        # Compute comprehensive risk metrics
        metrics = compute_risk_metrics(
            profit_distribution=profit_distribution,
            base_profit=base_profit,
            loss_threshold_pct=request.loss_threshold_pct,
            confidence_level=request.confidence_level,
        )

        logger.info(
            "Monte Carlo complete: %d iterations, VaR=%.2f, CVaR=%.2f",
            request.iterations,
            metrics["var_95"],
            metrics["cvar_95"],
        )

        return MonteCarloResponse(
            iterations=request.iterations,
            base_currency=base_currency,
            risk_metrics=metrics,
            profit_percentiles={
                "p5": metrics["p5_profit"],
                "p25": metrics["p25_profit"],
                "p50": metrics["median_profit"],
                "p75": metrics["p75_profit"],
                "p95": metrics["p95_profit"],
            },
            distribution_sample=profit_distribution[:100],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )
