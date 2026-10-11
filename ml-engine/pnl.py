from typing import List, Dict
from exposure import Exposure


def compute_pnl(exposures: List[Exposure], fx_rates: Dict[str, float], base_currency: str) -> Dict[str, float]:
    """
    Computes total revenue, total cost, profit, and margin in base currency.

    Args:
        exposures: List of Exposure objects.
        fx_rates: Dictionary of FX rates (Base_Currency / Foreign_Currency).
        base_currency: The base currency code.

    Returns:
        Dictionary with 'total_revenue', 'total_cost', 'profit', and 'margin'.
    """
    total_revenue = 0.0
    total_cost = 0.0

    for exp in exposures:
        # Get the rate to convert foreign currency to base currency
        if exp.currency == base_currency:
            rate = 1.0
        else:
            # We assume fx_rates[currency] gives the amount of base_currency per 1 unit of foreign currency
            # Example: 1 USD = 0.92 EUR. If base is EUR, rate is 0.92.
            rate = fx_rates.get(exp.currency, 1.0)

        amount_in_base = exp.amount * rate

        if exp.exp_type == 'revenue':
            total_revenue += amount_in_base
        elif exp.exp_type == 'cost':
            total_cost += amount_in_base

    profit = total_revenue - total_cost
    margin = (profit / total_revenue) if total_revenue != 0 else 0.0

    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "profit": profit,
        "margin": margin
    }
