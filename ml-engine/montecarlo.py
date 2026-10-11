import numpy as np
from typing import List, Dict
from exposure import Exposure
from pnl import compute_pnl



def run_monte_carlo(
        exposures: List[Exposure],
        base_fx_rates: Dict[str, float],
        volatilities: Dict[str, float],
        base_currency: str,
        iterations: int = 1000
) -> List[float]:
    """
    Runs a Monte Carlo simulation to estimate profit distribution under random FX shocks.

    Args:
        exposures: List of exposures.
        base_fx_rates: Base FX rates.
        volatilities: Standard deviation of shocks for each currency.
        base_currency: The base currency.
        iterations: Number of simulation runs.

    Returns:
        List of profits from each iteration.
    """
    profit_distribution = []

    currencies = [c for c in base_fx_rates.keys() if c != base_currency]

    for _ in range(iterations):
        # Generate random shocks for each currency based on its volatility
        # Assuming normal distribution centered at 0
        shocked_rates = base_fx_rates.copy()
        for curr in currencies:
            vol = volatilities.get(curr, 0.05)
            shock = np.random.normal(0, vol)
            shocked_rates[curr] *= (1 + shock)

        pnl_results = compute_pnl(exposures, shocked_rates, base_currency)
        profit_distribution.append(pnl_results["profit"])

    return profit_distribution
