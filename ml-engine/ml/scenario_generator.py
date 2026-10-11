"""
Scenario Generator (Scaffold)
===============================

Placeholder module for ML-driven scenario generation.
In production, this would use PCA on historical FX returns
to generate statistically meaningful stress scenarios.

Current implementation generates simple random scenarios
for demonstration purposes.
"""

import logging
from typing import List, Dict, Optional

import numpy as np

from fx_risk_engine.models.scenario import FXScenario

logger = logging.getLogger(__name__)


def generate_random_scenarios(
    currencies: List[str],
    n_scenarios: int = 5,
    max_shock: float = 0.25,
    seed: Optional[int] = None,
) -> List[FXScenario]:
    """
    Generate random FX shock scenarios.

    **Scaffold**: Uses uniform random shocks. In production, this
    would use PCA-based decomposition of historical return covariance.

    Args:
        currencies: List of currency codes to generate shocks for.
        n_scenarios: Number of scenarios to generate.
        max_shock: Maximum absolute shock magnitude.
        seed: Random seed for reproducibility.

    Returns:
        List of generated FXScenario objects.

    TODO:
        - Implement PCA on historical correlation matrix
        - Generate scenarios along principal component directions
        - Weight scenarios by eigenvalue (explained variance)
        - Support conditional scenario generation (given macro factors)
    """
    if seed is not None:
        np.random.seed(seed)

    scenarios: List[FXScenario] = []
    for i in range(n_scenarios):
        shocks = {
            ccy: round(float(np.random.uniform(-max_shock, max_shock)), 4)
            for ccy in currencies
        }
        scenario = FXScenario(
            name=f"Generated_Scenario_{i + 1}",
            shock_percentages=shocks,
            description=f"Auto-generated scenario #{i + 1}",
            created_by="scenario_generator",
        )
        scenarios.append(scenario)

    logger.info("Generated %d random scenarios for %s", n_scenarios, currencies)
    return scenarios


def generate_pca_scenarios(
    returns_matrix: Optional[np.ndarray] = None,
    currencies: Optional[List[str]] = None,
    n_components: int = 3,
    n_scenarios: int = 5,
) -> List[FXScenario]:
    """
    Generate scenarios based on PCA decomposition.

    **Scaffold**: Not yet implemented. Returns empty list.

    Args:
        returns_matrix: T×N matrix of historical returns.
        currencies: Currency labels for columns.
        n_components: Number of principal components to use.
        n_scenarios: Number of scenarios per component direction.

    Returns:
        List of FXScenario objects.

    TODO:
        - Compute covariance matrix from returns_matrix
        - Perform eigenvalue decomposition
        - Generate +/- shock scenarios along each PC direction
        - Scale shocks appropriately (e.g., 2-sigma moves)
    """
    logger.warning(
        "PCA scenario generation not yet implemented. "
        "Returning empty list."
    )
    return []
