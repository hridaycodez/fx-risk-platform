"""
Tests for FXScenario model.
"""

import pytest
from fx_risk_engine.models.scenario import FXScenario


class TestFXScenario:
    """Tests for the FXScenario dataclass."""

    def test_create_valid_scenario(self):
        """Create a valid scenario."""
        s = FXScenario("USD_Drop", {"USD": -0.15})
        assert s.name == "USD_Drop"
        assert s.shock_percentages == {"USD": -0.15}
        assert s.created_by == "system"

    def test_scenario_with_description(self):
        """Create scenario with description."""
        s = FXScenario("Test", {"USD": 0.10}, description="Test scenario")
        assert s.description == "Test scenario"

    def test_empty_name_raises(self):
        """Empty scenario name raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            FXScenario("", {"USD": 0.10})

    def test_empty_shocks_raises(self):
        """Empty shock dict raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            FXScenario("Test", {})

    def test_invalid_currency_code_raises(self):
        """Invalid currency code in shocks raises ValueError."""
        with pytest.raises(ValueError, match="3-letter"):
            FXScenario("Test", {"US": 0.10})

    def test_non_numeric_shock_raises(self):
        """Non-numeric shock value raises ValueError."""
        with pytest.raises(ValueError, match="numeric"):
            FXScenario("Test", {"USD": "bad"})

    def test_apply_shock(self):
        """Apply shock to base rates."""
        s = FXScenario("Test", {"USD": -0.10})
        base = {"USD": 0.92, "GBP": 1.15}
        shocked = s.apply_shock(base)
        assert shocked["USD"] == pytest.approx(0.828, rel=1e-3)
        assert shocked["GBP"] == 1.15  # unaffected

    def test_apply_shock_does_not_mutate_original(self):
        """Shock application returns new dict, doesn't modify original."""
        s = FXScenario("Test", {"USD": -0.10})
        base = {"USD": 0.92}
        shocked = s.apply_shock(base)
        assert base["USD"] == 0.92  # unchanged
        assert shocked["USD"] != base["USD"]

    def test_apply_shock_missing_currency(self):
        """Shock for non-existent currency is safely ignored."""
        s = FXScenario("Test", {"CHF": 0.10})
        base = {"USD": 0.92}
        shocked = s.apply_shock(base)
        assert shocked == base

    def test_multi_currency_shock(self):
        """Apply shocks to multiple currencies."""
        s = FXScenario("Multi", {"USD": -0.15, "GBP": 0.10})
        base = {"USD": 0.92, "GBP": 1.15, "JPY": 0.0062}
        shocked = s.apply_shock(base)
        assert shocked["USD"] == pytest.approx(0.782, rel=1e-3)
        assert shocked["GBP"] == pytest.approx(1.265, rel=1e-3)
        assert shocked["JPY"] == 0.0062

    def test_impact_summary(self):
        """Impact summary shows base and shocked rates."""
        s = FXScenario("Test", {"USD": -0.10})
        base = {"USD": 0.92, "GBP": 1.15}
        summary = s.impact_summary(base)
        assert "USD" in summary
        assert summary["USD"]["base_rate"] == 0.92
        assert summary["USD"]["change_pct"] == -10.0

    def test_to_dict(self):
        """Serialize scenario to dict."""
        s = FXScenario("Test", {"USD": 0.10}, description="desc")
        d = s.to_dict()
        assert d["name"] == "Test"
        assert d["shock_percentages"] == {"USD": 0.10}
        assert d["description"] == "desc"
        assert "created_at" in d

    def test_from_dict(self):
        """Deserialize scenario from dict."""
        data = {
            "name": "Test",
            "shock_percentages": {"USD": -0.15},
            "description": "From dict",
        }
        s = FXScenario.from_dict(data)
        assert s.name == "Test"
        assert s.shock_percentages == {"USD": -0.15}
        assert s.description == "From dict"

    def test_repr(self):
        """String representation includes name and shocks."""
        s = FXScenario("Test", {"USD": -0.10})
        r = repr(s)
        assert "Test" in r
        assert "USD" in r
