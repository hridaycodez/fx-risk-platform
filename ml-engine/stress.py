import numpy as np
from typing import List, Dict


def compute_risk_metrics(profit_distribution: List[float], base_profit: float, loss_threshold_pct: float) -> Dict:
    """
    Computes summary statistics and downside risk metrics.

    Args:
        profit_distribution: List of profits from simulation.
        base_profit: The profit in the base case scenario.
        loss_threshold_pct: Percentage drop from base profit to consider a 'significant loss'.

    Returns:
        Dictionary of risk metrics.
    """
    dist = np.array(profit_distribution)

    mean_profit = np.mean(dist)
    p5 = np.percentile(dist, 5)
    p95 = np.percentile(dist, 95)

    # Simple downside check: % of scenarios with profit drop > X%
    threshold_value = base_profit * (1 - loss_threshold_pct / 100.0)
    downside_scenarios = np.sum(dist < threshold_value)
    downside_probability = (downside_scenarios / len(profit_distribution)) * 100.0

    return {
        "mean_profit": mean_profit,
        "p5_profit": p5,
        "p95_profit": p95,
        "downside_probability": downside_probability,
        "loss_threshold_value": threshold_value
    }
