"""
montecarlo_stream.py — Streaming Monte Carlo Simulation
=========================================================
Upgraded Monte Carlo engine that:
  1. Uses live FX rates as base case (via data/live_rates.py)
  2. Supports correlated shocks via Cholesky decomposition
  3. Yields results in CHUNKS for real-time WebSocket streaming
  4. Computes all risk metrics at completion (VaR, CVaR, Sharpe, etc.)

The streaming approach is what makes the React chart "animate live".
"""

import numpy as np
import logging
from typing import List, Dict, Generator, Tuple, Optional

import config

logger = logging.getLogger("fx_risk_engine.montecarlo_stream")

# Currency order must match CORRELATION_MATRIX row/column order
CORR_CURRENCY_ORDER = ["USD", "GBP", "INR", "AED", "JPY", "CHF"]


def _compute_pnl(exposures: List[Dict], fx_rates: Dict[str, float], base_currency: str) -> float:
    """
    Fast inline PnL computation for Monte Carlo inner loop.
    Revenue exposures are POSITIVE, cost exposures are NEGATIVE.
    """
    total = 0.0
    for exp in exposures:
        currency = exp["currency"]
        amount = exp["amount"]
        exp_type = exp.get("exp_type", exp.get("expType", "revenue"))

        if currency == base_currency:
            rate = 1.0
        else:
            rate = fx_rates.get(currency, 1.0)

        # For EUR-base: rate = EUR per 1 unit of foreign currency
        # So value in EUR = amount * (1/rate) when rates are expressed as EUR=1
        # But our rates are already "how many foreign per 1 EUR"
        # So: value_in_EUR = amount / rate
        value_in_base = amount / rate

        if exp_type == "revenue":
            total += value_in_base
        else:
            total -= value_in_base

    return total


def run_correlated_monte_carlo(
    exposures: List[Dict],
    base_fx_rates: Dict[str, float],
    fx_volatility: Dict[str, float],
    base_currency: str = "EUR",
    iterations: int = 5000,
    seed: Optional[int] = None,
    chunk_size: int = 500,
) -> Generator[Tuple[str, object], None, None]:
    """
    Correlated Monte Carlo simulation — yields streaming chunks then final metrics.

    Yields:
        ("chunk", {"profits": [...], "progress": float})  — emitted every chunk_size iterations
        ("complete", {metrics dict})                        — emitted once at the end

    Correlated shocks via Cholesky decomposition:
        - AED moves almost identically to USD (USD-peg)
        - CHF & JPY strengthen when USD weakens (safe-haven)
        - INR weakens when USD strengthens (EM correlation)
    """
    if seed is not None:
        np.random.seed(seed)

    # Build volatility vector in CORR_CURRENCY_ORDER
    vol_vector = np.array([
        fx_volatility.get(ccy, config.FX_VOLATILITY.get(ccy, 0.05))
        for ccy in CORR_CURRENCY_ORDER
    ])

    profit_distribution = []
    chunk_buffer = []

    for i in range(iterations):
        # Generate correlated standard normal shocks
        z = np.random.standard_normal(len(CORR_CURRENCY_ORDER))
        correlated_z = config.CHOLESKY_MATRIX @ z  # apply correlation

        # Scale by each currency's volatility to get % shocks
        pct_shocks = correlated_z * vol_vector

        # Apply shocks to base rates
        shocked_rates = dict(base_fx_rates)
        for j, ccy in enumerate(CORR_CURRENCY_ORDER):
            if ccy in shocked_rates:
                shocked_rates[ccy] = shocked_rates[ccy] * (1 + pct_shocks[j])

        profit = _compute_pnl(exposures, shocked_rates, base_currency)
        profit_distribution.append(profit)
        chunk_buffer.append(profit)

        # Yield chunk every `chunk_size` iterations
        if len(chunk_buffer) >= chunk_size:
            progress = (i + 1) / iterations
            yield ("chunk", {
                "profits": chunk_buffer,
                "progress": round(progress, 4),
                "iteration": i + 1,
            })
            chunk_buffer = []

    # Yield any remaining
    if chunk_buffer:
        yield ("chunk", {
            "profits": chunk_buffer,
            "progress": 1.0,
            "iteration": iterations,
        })

    # Compute final risk metrics and yield "complete"
    profits_array = np.array(profit_distribution)
    metrics = _compute_risk_metrics(profits_array, base_currency)
    yield ("complete", metrics)


def _compute_risk_metrics(profits: np.ndarray, base_currency: str) -> Dict:
    """Compute all statistical risk metrics from the profit distribution."""
    mean_profit = float(np.mean(profits))
    std_profit  = float(np.std(profits))

    # VaR at 95% confidence — worst 5th percentile
    var_95 = float(np.percentile(profits, 5))

    # CVaR (Expected Shortfall) — average of losses beyond VaR
    tail_losses = profits[profits <= var_95]
    cvar_95 = float(np.mean(tail_losses)) if len(tail_losses) > 0 else var_95

    p95_profit  = float(np.percentile(profits, 95))
    p5_profit   = float(np.percentile(profits, 5))

    # Downside probability — P(loss > 20% of mean)
    threshold = mean_profit * (1 - config.LOSS_THRESHOLD_PERCENT / 100)
    downside_prob = float(np.mean(profits < threshold) * 100)

    # Sharpe-like ratio (mean / std)
    sharpe = float(mean_profit / std_profit) if std_profit > 0 else 0.0

    # Skewness and Kurtosis
    from scipy import stats as scipy_stats
    skewness = float(scipy_stats.skew(profits))
    kurt     = float(scipy_stats.kurtosis(profits))

    # ML Risk Level classification
    risk_level = _classify_risk(downside_prob, var_95, mean_profit)

    return {
        "base_currency": base_currency,
        "iterations": len(profits),
        "mean_profit": round(mean_profit, 2),
        "std_profit": round(std_profit, 2),
        "var_95": round(var_95, 2),
        "cvar_95": round(cvar_95, 2),
        "p5_profit": round(p5_profit, 2),
        "p95_profit": round(p95_profit, 2),
        "downside_probability": round(downside_prob, 2),
        "sharpe_ratio": round(sharpe, 4),
        "skewness": round(skewness, 4),
        "kurtosis": round(kurt, 4),
        "risk_level": risk_level,
    }


def _classify_risk(downside_prob: float, var_95: float, mean_profit: float) -> str:
    """
    Classifies portfolio risk:
      - LOW: Steady profit, worst 5% outcome is within 25% of mean, downside probability < 15%
      - MEDIUM: Moderate swings, 25-50% profit drop in worst 5%, or downside prob 15-30%
      - HIGH: Severe risk, worst 5% wipes >50% profit or turns negative (loss), or downside prob > 30%
    """
    if abs(mean_profit) < 1e-6:
        return "HIGH" if var_95 < 0 else "MEDIUM"

    # Worst case (5th percentile) actually results in a net negative loss:
    if var_95 < 0:
        capital_loss_ratio = abs(var_95) / abs(mean_profit)
        if capital_loss_ratio > 0.15 or downside_prob > 25:
            return "HIGH"
        return "MEDIUM"

    # If var_95 is positive, compute the percentage drop from expected profit:
    profit_drop_ratio = (mean_profit - var_95) / mean_profit if mean_profit > 0 else 0

    if downside_prob > 30 or profit_drop_ratio > 0.50:
        return "HIGH"
    elif downside_prob > 15 or profit_drop_ratio > 0.25:
        return "MEDIUM"
    else:
        return "LOW"
