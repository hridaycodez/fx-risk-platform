"""
Stress Testing Engine
=====================

Scenario management with audit trail. Provides pre-defined stress scenarios,
custom scenario creation, and batch stress testing with comparison reports.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.models.scenario import FXScenario
from fx_risk_engine.analytics.pnl import compute_pnl

logger = logging.getLogger(__name__)


# Pre-defined stress scenarios commonly used in FX risk management
PREDEFINED_SCENARIOS: List[FXScenario] = [
    FXScenario(
        name="USD_Crash",
        shock_percentages={"USD": -0.20},
        description="US Dollar depreciates 20% against base currency",
        created_by="system",
    ),
    FXScenario(
        name="GBP_Brexit_Shock",
        shock_percentages={"GBP": -0.15},
        description="British Pound drops 15% (Brexit-style event)",
        created_by="system",
    ),
    FXScenario(
        name="JPY_Surge",
        shock_percentages={"JPY": 0.25},
        description="Japanese Yen appreciates 25% (safe-haven rally)",
        created_by="system",
    ),
    FXScenario(
        name="Global_Risk_Off",
        shock_percentages={"USD": -0.10, "GBP": -0.12, "JPY": 0.15},
        description="Global risk-off: USD/GBP weaken, JPY strengthens",
        created_by="system",
    ),
    FXScenario(
        name="EM_Currency_Crisis",
        shock_percentages={"USD": 0.05, "GBP": -0.08, "JPY": 0.10},
        description="Emerging market contagion with flight to safety",
        created_by="system",
    ),
]


class ScenarioManager:
    """
    Manages FX scenarios with audit trail and batch execution.
    """

    def __init__(self) -> None:
        """Initialize with pre-defined scenarios."""
        self._scenarios: Dict[str, FXScenario] = {}
        # Load pre-defined scenarios
        for scenario in PREDEFINED_SCENARIOS:
            self._scenarios[scenario.name] = scenario

    def add_scenario(self, scenario: FXScenario) -> None:
        """Add or update a scenario."""
        logger.info("Adding scenario: %s", scenario.name)
        self._scenarios[scenario.name] = scenario

    def get_scenario(self, name: str) -> Optional[FXScenario]:
        """Retrieve a scenario by name."""
        return self._scenarios.get(name)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all available scenarios with metadata."""
        return [s.to_dict() for s in self._scenarios.values()]

    def remove_scenario(self, name: str) -> bool:
        """Remove a scenario by name. Returns True if removed."""
        if name in self._scenarios:
            del self._scenarios[name]
            return True
        return False

    @property
    def scenario_count(self) -> int:
        """Number of registered scenarios."""
        return len(self._scenarios)


def run_stress_test(
    exposures: List[Exposure],
    base_fx_rates: Dict[str, float],
    base_currency: str,
    scenario: FXScenario,
) -> Dict[str, Any]:
    """
    Run a single stress test scenario.

    Args:
        exposures: List of exposures.
        base_fx_rates: Base FX rates.
        base_currency: Company's base currency.
        scenario: The stress scenario to apply.

    Returns:
        Dict with base_case, stress_case, and impact analysis.
    """
    base_result = compute_pnl(exposures, base_fx_rates, base_currency)
    shocked_rates = scenario.apply_shock(base_fx_rates)
    stress_result = compute_pnl(exposures, shocked_rates, base_currency)

    delta_profit = stress_result["profit"] - base_result["profit"]
    delta_pct = (
        (delta_profit / abs(base_result["profit"]) * 100)
        if base_result["profit"] != 0
        else 0.0
    )

    return {
        "scenario_name": scenario.name,
        "scenario_description": scenario.description,
        "base_profit": round(base_result["profit"], 2),
        "stress_profit": round(stress_result["profit"], 2),
        "delta_profit": round(delta_profit, 2),
        "delta_pct": round(delta_pct, 2),
        "shocked_rates": shocked_rates,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_batch_stress_test(
    exposures: List[Exposure],
    base_fx_rates: Dict[str, float],
    base_currency: str,
    scenarios: Optional[List[FXScenario]] = None,
) -> Dict[str, Any]:
    """
    Run stress tests across multiple scenarios.

    Args:
        exposures: List of exposures.
        base_fx_rates: Base FX rates.
        base_currency: Company's base currency.
        scenarios: List of scenarios. Defaults to predefined scenarios.

    Returns:
        Dict with base case, ordered results, worst/best scenario.
    """
    if scenarios is None:
        scenarios = PREDEFINED_SCENARIOS

    base_result = compute_pnl(exposures, base_fx_rates, base_currency)
    results: List[Dict[str, Any]] = []

    for scenario in scenarios:
        result = run_stress_test(
            exposures, base_fx_rates, base_currency, scenario
        )
        results.append(result)

    # Sort by impact (worst first)
    results.sort(key=lambda r: r["delta_profit"])

    return {
        "base_profit": round(base_result["profit"], 2),
        "num_scenarios": len(results),
        "results": results,
        "worst_scenario": results[0]["scenario_name"] if results else None,
        "best_scenario": results[-1]["scenario_name"] if results else None,
    }
