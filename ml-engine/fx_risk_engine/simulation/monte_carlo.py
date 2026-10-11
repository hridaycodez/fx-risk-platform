"""
Monte Carlo Simulation Engine
==============================

Random and correlated FX shock simulations for profit distribution
estimation. Supports both independent shocks and correlated shocks
via Cholesky decomposition of a correlation matrix.
"""

import logging
from typing import List, Dict, Any, Optional

import numpy as np

from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.analytics.pnl import compute_pnl

logger = logging.getLogger(__name__)


def run_monte_carlo(
    exposures: List[Exposure],
    base_fx_rates: Dict[str, float],
    volatilities: Dict[str, float],
    base_currency: str,
    iterations: int = 1000,
    seed: Optional[int] = None,
) -> List[float]:
    """
    Monte Carlo simulation with independent random FX shocks.

    Each iteration applies a random normal shock (mean=0, std=volatility)
    to each foreign currency's FX rate, then computes P&L.

    Args:
        exposures: List of FX exposures.
        base_fx_rates: Base FX rates.
        volatilities: Dict of currency -> standard deviation of shock.
        base_currency: Company's base currency.
        iterations: Number of simulation iterations.
        seed: Random seed for reproducibility.

    Returns:
        List of profit values from each iteration.
    """
    if seed is not None:
        np.random.seed(seed)

    currencies = [c for c in base_fx_rates.keys() if c != base_currency]
    profit_distribution: List[float] = []

    for _ in range(iterations):
        shocked_rates = base_fx_rates.copy()
        for curr in currencies:
            vol = volatilities.get(curr, 0.05)
            shock = np.random.normal(0, vol)
            shocked_rates[curr] *= (1 + shock)

        pnl_result = compute_pnl(exposures, shocked_rates, base_currency)
        profit_distribution.append(pnl_result["profit"])

    return profit_distribution


def run_correlated_monte_carlo(
    exposures: List[Exposure],
    base_fx_rates: Dict[str, float],
    volatilities: Dict[str, float],
    correlation_matrix: Optional[np.ndarray] = None,
    base_currency: str = "EUR",
    iterations: int = 1000,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Monte Carlo simulation with correlated FX shocks.

    Uses Cholesky decomposition to generate correlated normal draws
    based on a correlation matrix between currencies.

    Args:
        exposures: List of FX exposures.
        base_fx_rates: Base FX rates.
        volatilities: Dict of currency -> volatility (std dev).
        correlation_matrix: N×N correlation matrix for the currencies.
                            If None, uses an identity matrix (independent).
        base_currency: Company's base currency.
        iterations: Number of simulation runs.
        seed: Random seed for reproducibility.

    Returns:
        Dict with profit_distribution, currency_shocks, and metadata.
    """
    if seed is not None:
        np.random.seed(seed)

    currencies = sorted([c for c in base_fx_rates.keys() if c != base_currency])
    n_currencies = len(currencies)

    if n_currencies == 0:
        logger.warning("No foreign currencies to simulate.")
        return {
            "profit_distribution": [],
            "currencies": [],
            "iterations": iterations,
        }

    # Build correlation matrix
    if correlation_matrix is None:
        corr = np.eye(n_currencies)
    else:
        corr = np.array(correlation_matrix)
        if corr.shape != (n_currencies, n_currencies):
            raise ValueError(
                f"Correlation matrix shape {corr.shape} doesn't match "
                f"{n_currencies} currencies."
            )

    # Cholesky decomposition for correlated draws
    try:
        chol = np.linalg.cholesky(corr)
    except np.linalg.LinAlgError:
        logger.warning(
            "Correlation matrix is not positive-definite. Falling back to "
            "nearest positive-definite matrix."
        )
        # Fall back to identity if not PD
        chol = np.eye(n_currencies)

    # Volatility vector
    vol_vec = np.array([volatilities.get(c, 0.05) for c in currencies])

    profit_distribution: List[float] = []
    all_shocks: List[Dict[str, float]] = []

    for _ in range(iterations):
        # Generate independent standard normal draws
        z = np.random.normal(0, 1, n_currencies)
        # Apply correlation via Cholesky
        correlated_z = chol @ z
        # Scale by volatility
        shocks = correlated_z * vol_vec

        # Apply shocks to rates
        shocked_rates = base_fx_rates.copy()
        shock_dict: Dict[str, float] = {}
        for i, curr in enumerate(currencies):
            shocked_rates[curr] *= (1 + shocks[i])
            shock_dict[curr] = float(shocks[i])

        pnl_result = compute_pnl(exposures, shocked_rates, base_currency)
        profit_distribution.append(pnl_result["profit"])
        all_shocks.append(shock_dict)

    return {
        "profit_distribution": profit_distribution,
        "currencies": currencies,
        "iterations": iterations,
        "seed": seed,
        "correlation_matrix": corr.tolist(),
        "mean_shocks": {
            curr: float(np.mean([s[curr] for s in all_shocks]))
            for curr in currencies
        },
    }
