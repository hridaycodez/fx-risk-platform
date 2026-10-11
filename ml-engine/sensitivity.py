from typing import List, Dict
import numpy as np
from exposure import Exposure
from pnl import compute_pnl


def run_sensitivity_analysis(
        exposures: List[Exposure],
        base_fx_rates: Dict[str, float],
        target_currency: str,
        base_currency: str,
        shock_range: List[float] = None
) -> List[Dict]:
    """
    Performs one-variable sensitivity analysis for a specific currency.

    Args:
        exposures: List of exposures.
        base_fx_rates: Base FX rates.
        target_currency: The currency to shock (e.g., 'USD').
        base_currency: The base currency of the company.
        shock_range: List of shock percentages (e.g., [-0.2, -0.1, 0, 0.1, 0.2]).

    Returns:
        List of results containing shock percentage and resulting profit.
    """
    if shock_range is None:
        shock_range = list(np.linspace(-0.2, 0.2, 9))  # -20% to +20% in 5% steps

    results = []

    for shock in shock_range:
        # Create a temporary shocked rate dictionary
        shocked_rates = base_fx_rates.copy()
        if target_currency in shocked_rates:
            shocked_rates[target_currency] *= (1 + shock)

        pnl_results = compute_pnl(exposures, shocked_rates, base_currency)

        results.append({
            "shock_percent": shock,
            "profit": pnl_results["profit"]
        })

    return results
