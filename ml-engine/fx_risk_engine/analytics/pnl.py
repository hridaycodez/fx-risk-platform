"""
PnL Engine
==========

Computes profit and loss across single or multiple FX scenarios.
Supports base case analysis, multi-scenario comparison, and
detailed per-exposure P&L breakdowns.
"""

import logging
from typing import List, Dict, Any, Optional

from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.models.scenario import FXScenario

logger = logging.getLogger(__name__)


class PnLEngine:
    """
    Profit & Loss computation engine for FX exposures.

    Computes revenue, cost, profit, and margin in a specified
    base currency using provided FX rates.
    """

    def __init__(
        self,
        exposures: List[Exposure],
        base_fx_rates: Dict[str, float],
        base_currency: str,
    ) -> None:
        """
        Initialize PnL engine.

        Args:
            exposures: List of company FX exposures.
            base_fx_rates: Base FX rates (currency -> rate in base currency).
            base_currency: The company's reporting currency.
        """
        self.exposures = exposures
        self.base_fx_rates = base_fx_rates
        self.base_currency = base_currency

    def compute(
        self,
        fx_rates: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute P&L using the given (or base) FX rates.

        Args:
            fx_rates: Optional overriding FX rates. If None, uses base rates.

        Returns:
            Dictionary with total_revenue, total_cost, profit, margin,
            and per-exposure breakdown.
        """
        rates = fx_rates if fx_rates is not None else self.base_fx_rates
        total_revenue = 0.0
        total_cost = 0.0
        breakdown: List[Dict[str, Any]] = []

        # Detect quote convention (e.g. Frankfurter / ECB rates where EUR=1.00 and JPY>5, INR>5, USD>1.05)
        is_indirect = any(
            (ccy in ("JPY", "INR", "AED") and r > 2.0)
            or (ccy == "USD" and r > 1.05 and rates.get("GBP", 1.0) < 0.95)
            for ccy, r in rates.items()
        )

        for exp in self.exposures:
            if exp.currency == self.base_currency:
                rate = 1.0
                amount_in_base = exp.amount
            else:
                rate = rates.get(exp.currency)
                if rate is None or rate == 0:
                    logger.warning(
                        "No FX rate for '%s'; defaulting to 1.0", exp.currency
                    )
                    rate = 1.0

                if is_indirect:
                    # Foreign currency per 1 base unit (e.g. 1.08 USD per 1 EUR)
                    amount_in_base = exp.amount / rate
                else:
                    # Base currency per 1 foreign unit (e.g. 0.92 EUR per 1 USD)
                    amount_in_base = exp.amount * rate

            if exp.exp_type == "revenue":
                total_revenue += amount_in_base
            else:
                total_cost += amount_in_base

            breakdown.append({
                "name": exp.name,
                "type": exp.exp_type,
                "original_amount": exp.amount,
                "currency": exp.currency,
                "fx_rate": rate,
                "amount_in_base": amount_in_base,
            })

        profit = total_revenue - total_cost
        margin = (profit / total_revenue) if total_revenue != 0 else 0.0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "profit": round(profit, 2),
            "margin": round(margin, 6),
            "base_currency": self.base_currency,
            "breakdown": breakdown,
        }

    def compute_scenario(self, scenario: FXScenario) -> Dict[str, Any]:
        """
        Compute P&L under a specific shock scenario.

        Args:
            scenario: FXScenario instance with shock percentages.

        Returns:
            Dict with scenario details, P&L results, and delta from base.
        """
        base_result = self.compute()
        shocked_rates = scenario.apply_shock(self.base_fx_rates)
        scenario_result = self.compute(fx_rates=shocked_rates)

        delta_profit = scenario_result["profit"] - base_result["profit"]
        delta_margin = scenario_result["margin"] - base_result["margin"]

        return {
            "scenario_name": scenario.name,
            "scenario_description": scenario.description,
            "base_case": base_result,
            "scenario_case": scenario_result,
            "delta_profit": round(delta_profit, 2),
            "delta_margin": round(delta_margin, 6),
        }

    def compute_multi_scenario(
        self, scenarios: List[FXScenario]
    ) -> Dict[str, Any]:
        """
        Run P&L across multiple scenarios and compare.

        Args:
            scenarios: List of FXScenario instances.

        Returns:
            Dict with base case and list of scenario results, sorted by
            impact (worst-first).
        """
        base_result = self.compute()
        results: List[Dict[str, Any]] = []

        for scenario in scenarios:
            res = self.compute_scenario(scenario)
            results.append({
                "scenario_name": res["scenario_name"],
                "profit": res["scenario_case"]["profit"],
                "delta_profit": res["delta_profit"],
                "delta_margin": res["delta_margin"],
            })

        # Sort by impact (worst delta first)
        results.sort(key=lambda r: r["delta_profit"])

        return {
            "base_case": base_result,
            "scenarios": results,
            "worst_case": results[0] if results else None,
            "best_case": results[-1] if results else None,
        }


def compute_pnl(
    exposures: List[Exposure],
    fx_rates: Dict[str, float],
    base_currency: str,
) -> Dict[str, float]:
    """
    Standalone convenience function for P&L computation.

    This is a backward-compatible wrapper around PnLEngine.compute().

    Args:
        exposures: List of Exposure objects.
        fx_rates: Dictionary of FX rates.
        base_currency: The base currency code.

    Returns:
        Dictionary with total_revenue, total_cost, profit, and margin.
    """
    engine = PnLEngine(exposures, fx_rates, base_currency)
    result = engine.compute()
    # Return simplified dict for backward compatibility
    return {
        "total_revenue": result["total_revenue"],
        "total_cost": result["total_cost"],
        "profit": result["profit"],
        "margin": result["margin"],
    }
