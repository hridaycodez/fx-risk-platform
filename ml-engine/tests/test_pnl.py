"""
Tests for PnL Engine.
"""

import pytest
from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.models.scenario import FXScenario
from fx_risk_engine.analytics.pnl import PnLEngine, compute_pnl


BASE_RATES = {"USD": 0.92, "GBP": 1.15, "JPY": 0.0062}
BASE_CURRENCY = "EUR"


def _sample_exposures():
    """Get sample exposures."""
    return [
        Exposure("US_Sales", "revenue", 500000, "USD"),
        Exposure("UK_Sales", "revenue", 200000, "GBP"),
        Exposure("EU_Ops", "cost", 300000, "EUR"),
        Exposure("JP_Parts", "cost", 10000000, "JPY"),
    ]


class TestComputePnl:
    """Tests for the standalone compute_pnl function."""

    def test_base_case_profit(self):
        """Base case returns positive profit for sample data."""
        result = compute_pnl(_sample_exposures(), BASE_RATES, BASE_CURRENCY)
        assert "profit" in result
        assert "total_revenue" in result
        assert "total_cost" in result
        assert "margin" in result
        assert result["total_revenue"] > 0
        assert result["total_cost"] > 0

    def test_revenue_calculation(self):
        """Revenue is correctly summed in base currency."""
        exposures = [Exposure("single", "revenue", 1000, "USD")]
        result = compute_pnl(exposures, {"USD": 0.92}, "EUR")
        assert result["total_revenue"] == pytest.approx(920.0, rel=1e-3)

    def test_cost_calculation(self):
        """Cost is correctly summed in base currency."""
        exposures = [Exposure("single", "cost", 1000, "USD")]
        result = compute_pnl(exposures, {"USD": 0.92}, "EUR")
        assert result["total_cost"] == pytest.approx(920.0, rel=1e-3)
        assert result["profit"] == pytest.approx(-920.0, rel=1e-3)

    def test_base_currency_exposure(self):
        """Exposure in base currency uses rate 1.0."""
        exposures = [Exposure("Local", "revenue", 1000, "EUR")]
        result = compute_pnl(exposures, BASE_RATES, "EUR")
        assert result["total_revenue"] == 1000.0

    def test_margin_calculation(self):
        """Margin = profit / revenue."""
        exposures = [
            Exposure("rev", "revenue", 1000, "EUR"),
            Exposure("cost", "cost", 400, "EUR"),
        ]
        result = compute_pnl(exposures, {}, "EUR")
        assert result["margin"] == pytest.approx(0.6, rel=1e-3)

    def test_zero_revenue_margin(self):
        """Zero revenue results in zero margin (no division by zero)."""
        exposures = [Exposure("cost", "cost", 1000, "EUR")]
        result = compute_pnl(exposures, {}, "EUR")
        assert result["margin"] == 0.0

    def test_empty_exposures(self):
        """Empty exposure list returns zeros."""
        result = compute_pnl([], BASE_RATES, BASE_CURRENCY)
        assert result["profit"] == 0.0
        assert result["total_revenue"] == 0.0
        assert result["total_cost"] == 0.0


class TestPnLEngine:
    """Tests for the PnLEngine class."""

    def test_compute_default_rates(self):
        """PnLEngine.compute() uses base rates by default."""
        engine = PnLEngine(_sample_exposures(), BASE_RATES, BASE_CURRENCY)
        result = engine.compute()
        assert result["profit"] != 0
        assert result["base_currency"] == "EUR"
        assert "breakdown" in result

    def test_compute_override_rates(self):
        """PnLEngine.compute() with overridden rates."""
        engine = PnLEngine(_sample_exposures(), BASE_RATES, BASE_CURRENCY)
        new_rates = {"USD": 1.0, "GBP": 1.0, "JPY": 0.01}
        result = engine.compute(fx_rates=new_rates)
        assert result["profit"] != 0

    def test_compute_scenario(self):
        """PnLEngine.compute_scenario() returns delta."""
        engine = PnLEngine(_sample_exposures(), BASE_RATES, BASE_CURRENCY)
        scenario = FXScenario("Test", {"USD": -0.10})
        result = engine.compute_scenario(scenario)
        assert "delta_profit" in result
        assert "scenario_name" in result
        assert result["scenario_name"] == "Test"

    def test_compute_multi_scenario(self):
        """PnLEngine.compute_multi_scenario() compares scenarios."""
        engine = PnLEngine(_sample_exposures(), BASE_RATES, BASE_CURRENCY)
        scenarios = [
            FXScenario("USD_Drop", {"USD": -0.20}),
            FXScenario("GBP_Rise", {"GBP": 0.10}),
        ]
        result = engine.compute_multi_scenario(scenarios)
        assert "base_case" in result
        assert len(result["scenarios"]) == 2
        assert result["worst_case"] is not None
        assert result["best_case"] is not None
        # Sorted worst-first
        assert result["scenarios"][0]["delta_profit"] <= result["scenarios"][1]["delta_profit"]

    def test_breakdown_contains_all_exposures(self):
        """Breakdown has an entry for each exposure."""
        exposures = _sample_exposures()
        engine = PnLEngine(exposures, BASE_RATES, BASE_CURRENCY)
        result = engine.compute()
        assert len(result["breakdown"]) == len(exposures)
