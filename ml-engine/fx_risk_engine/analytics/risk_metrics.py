"""
Risk Metrics Engine
===================

Statistical risk metrics computed from Monte Carlo profit distributions.
Includes Value at Risk (VaR), Conditional VaR (CVaR / Expected Shortfall),
downside risk probability, and distribution summary statistics.
"""

import logging
from typing import List, Dict, Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


def compute_var(
    profit_distribution: List[float],
    confidence_level: float = 0.95,
) -> float:
    """
    Compute historical Value at Risk (VaR).

    VaR answers: "What is the maximum loss at a given confidence level?"

    Args:
        profit_distribution: Simulated profit values.
        confidence_level: Confidence level (e.g., 0.95 for 95% VaR).

    Returns:
        VaR as a positive number representing the potential loss.
    """
    if not profit_distribution:
        raise ValueError("Profit distribution must be non-empty.")

    dist = np.array(profit_distribution)
    percentile = (1 - confidence_level) * 100  # e.g., 5th percentile for 95% VaR
    var_value = np.percentile(dist, percentile)

    return round(float(var_value), 2)


def compute_cvar(
    profit_distribution: List[float],
    confidence_level: float = 0.95,
) -> float:
    """
    Compute Conditional Value at Risk (CVaR / Expected Shortfall).

    CVaR answers: "What is the average loss beyond the VaR threshold?"
    It is always worse than or equal to VaR.

    Args:
        profit_distribution: Simulated profit values.
        confidence_level: Confidence level (e.g., 0.95).

    Returns:
        CVaR as the mean of losses beyond the VaR threshold.
    """
    if not profit_distribution:
        raise ValueError("Profit distribution must be non-empty.")

    dist = np.array(profit_distribution)
    var_value = compute_var(profit_distribution, confidence_level)

    # Average of all values at or below VaR
    tail_losses = dist[dist <= var_value]
    if len(tail_losses) == 0:
        return var_value

    return round(float(np.mean(tail_losses)), 2)


def compute_downside_probability(
    profit_distribution: List[float],
    base_profit: float,
    loss_threshold_pct: float = 20.0,
) -> float:
    """
    Compute the probability of a significant downside event.

    Args:
        profit_distribution: Simulated profit values.
        base_profit: Base case profit.
        loss_threshold_pct: Percentage drop threshold (e.g., 20 means 20% drop).

    Returns:
        Probability as a percentage (0-100).
    """
    if not profit_distribution:
        raise ValueError("Profit distribution must be non-empty.")

    dist = np.array(profit_distribution)
    threshold_value = base_profit * (1 - loss_threshold_pct / 100.0)
    downside_count = int(np.sum(dist < threshold_value))
    probability = (downside_count / len(profit_distribution)) * 100.0

    return round(probability, 2)


def compute_risk_metrics(
    profit_distribution: List[float],
    base_profit: float,
    loss_threshold_pct: float = 20.0,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """
    Compute comprehensive risk metrics from a profit distribution.

    Args:
        profit_distribution: List of simulated profits (from Monte Carlo).
        base_profit: The profit in the base case scenario.
        loss_threshold_pct: Percentage drop threshold for downside risk.
        confidence_level: Confidence level for VaR/CVaR (default 95%).

    Returns:
        Dictionary of risk metrics including VaR, CVaR, distribution stats,
        and downside probability.
    """
    if not profit_distribution:
        raise ValueError("Profit distribution must be non-empty.")

    dist = np.array(profit_distribution)

    # Core distribution statistics
    mean_profit = float(np.mean(dist))
    std_profit = float(np.std(dist))
    median_profit = float(np.median(dist))
    min_profit = float(np.min(dist))
    max_profit = float(np.max(dist))

    # Percentiles
    p5 = float(np.percentile(dist, 5))
    p25 = float(np.percentile(dist, 25))
    p75 = float(np.percentile(dist, 75))
    p95 = float(np.percentile(dist, 95))

    # VaR and CVaR
    var_95 = compute_var(profit_distribution, confidence_level)
    cvar_95 = compute_cvar(profit_distribution, confidence_level)

    # Downside probability
    downside_prob = compute_downside_probability(
        profit_distribution, base_profit, loss_threshold_pct
    )

    # Loss threshold value
    threshold_value = base_profit * (1 - loss_threshold_pct / 100.0)

    # Profit-at-Risk (difference between base and VaR)
    profit_at_risk = base_profit - var_95

    # Sharpe-like ratio (profit / volatility)
    sharpe_like = (mean_profit / std_profit) if std_profit > 0 else 0.0

    # Skewness and kurtosis
    skewness = float(
        np.mean(((dist - mean_profit) / std_profit) ** 3)
    ) if std_profit > 0 else 0.0
    kurtosis = float(
        np.mean(((dist - mean_profit) / std_profit) ** 4) - 3
    ) if std_profit > 0 else 0.0

    return {
        # Distribution stats
        "mean_profit": round(mean_profit, 2),
        "median_profit": round(median_profit, 2),
        "std_profit": round(std_profit, 2),
        "min_profit": round(min_profit, 2),
        "max_profit": round(max_profit, 2),
        # Percentiles
        "p5_profit": round(p5, 2),
        "p25_profit": round(p25, 2),
        "p75_profit": round(p75, 2),
        "p95_profit": round(p95, 2),
        # Risk metrics
        "var_95": var_95,
        "cvar_95": cvar_95,
        "profit_at_risk": round(profit_at_risk, 2),
        # Downside
        "downside_probability": downside_prob,
        "loss_threshold_value": round(threshold_value, 2),
        # Shape
        "sharpe_like_ratio": round(sharpe_like, 4),
        "skewness": round(skewness, 4),
        "kurtosis": round(kurtosis, 4),
        # Meta
        "base_profit": round(base_profit, 2),
        "confidence_level": confidence_level,
        "num_simulations": len(profit_distribution),
    }
