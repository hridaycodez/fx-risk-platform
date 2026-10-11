"""
Sensitivity Engine
==================

Per-currency and multi-currency sensitivity analysis.
Sweeps FX rates across a shock range and measures the
resulting impact on P&L.
"""

import logging
from typing import List, Dict, Any, Optional

import numpy as np

from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.analytics.pnl import compute_pnl

logger = logging.getLogger(__name__)


def run_sensitivity_analysis(
    exposures: List[Exposure],
    base_fx_rates: Dict[str, float],
    target_currency: str,
    base_currency: str,
    shock_range: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """
    Single-currency sensitivity analysis.

    Shocks one currency across a range and measures profit change.

    Args:
        exposures: List of exposures.
        base_fx_rates: Base FX rates.
        target_currency: Currency to shock (e.g., 'USD').
        base_currency: Company's base currency.
        shock_range: List of shock decimals. Defaults to -20% to +20% in 5% steps.

    Returns:
        List of dicts with shock_percent, profit, delta_profit.
    """
    if shock_range is None:
        shock_range = list(np.linspace(-0.20, 0.20, 9))

    # Base case profit
    base_result = compute_pnl(exposures, base_fx_rates, base_currency)
    base_profit = base_result["profit"]

    results: List[Dict[str, Any]] = []

    for shock in shock_range:
        shocked_rates = base_fx_rates.copy()
        if target_currency in shocked_rates:
            shocked_rates[target_currency] *= (1 + shock)

        pnl_result = compute_pnl(exposures, shocked_rates, base_currency)
        profit = pnl_result["profit"]

        results.append({
            "currency": target_currency,
            "shock_percent": round(shock, 4),
            "profit": round(profit, 2),
            "delta_profit": round(profit - base_profit, 2),
            "delta_pct": round(
                ((profit - base_profit) / abs(base_profit) * 100)
                if base_profit != 0
                else 0.0,
                2,
            ),
        })

    return results


def run_multi_currency_sensitivity(
    exposures: List[Exposure],
    base_fx_rates: Dict[str, float],
    base_currency: str,
    currencies: Optional[List[str]] = None,
    shock_range: Optional[List[float]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Multi-currency sensitivity analysis.

    Runs sensitivity analysis for each specified currency independently.

    Args:
        exposures: List of exposures.
        base_fx_rates: Base FX rates.
        base_currency: Company's base currency.
        currencies: List of currencies to analyze. If None, analyzes all
                     non-base currencies present in the exposures.
        shock_range: Shock range per currency.

    Returns:
        Dict mapping currency -> list of sensitivity results.
    """
    if currencies is None:
        currencies = list({
            exp.currency
            for exp in exposures
            if exp.currency != base_currency and exp.currency in base_fx_rates
        })
        currencies.sort()

    results: Dict[str, List[Dict[str, Any]]] = {}

    for ccy in currencies:
        logger.info("Running sensitivity for %s", ccy)
        results[ccy] = run_sensitivity_analysis(
            exposures, base_fx_rates, ccy, base_currency, shock_range
        )

    return results


def compute_sensitivity_summary(
    sensitivity_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Summarize sensitivity results for a single currency.

    Args:
        sensitivity_results: Output from run_sensitivity_analysis.

    Returns:
        Dict with min/max/range profit stats and the most impactful shock.
    """
    if not sensitivity_results:
        return {}

    profits = [r["profit"] for r in sensitivity_results]
    deltas = [abs(r["delta_profit"]) for r in sensitivity_results]

    max_impact_idx = int(np.argmax(deltas))

    return {
        "currency": sensitivity_results[0]["currency"],
        "min_profit": min(profits),
        "max_profit": max(profits),
        "profit_range": max(profits) - min(profits),
        "most_impactful_shock": sensitivity_results[max_impact_idx]["shock_percent"],
        "max_delta": sensitivity_results[max_impact_idx]["delta_profit"],
    }
