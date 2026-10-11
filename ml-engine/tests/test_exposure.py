"""
Tests for Exposure and CompanyFXProfile models.
"""

import pytest
from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.models.profile import CompanyFXProfile


# ── Exposure Tests ────────────────────────────────────────────────────

class TestExposure:
    """Tests for the Exposure dataclass."""

    def test_valid_revenue_exposure(self):
        """Create a valid revenue exposure."""
        exp = Exposure("US_Sales", "revenue", 500000, "USD")
        assert exp.name == "US_Sales"
        assert exp.exp_type == "revenue"
        assert exp.amount == 500000
        assert exp.currency == "USD"
        assert exp.sign == 1.0

    def test_valid_cost_exposure(self):
        """Create a valid cost exposure."""
        exp = Exposure("JP_Parts", "cost", 10000000, "JPY")
        assert exp.exp_type == "cost"
        assert exp.sign == -1.0

    def test_currency_normalized_to_uppercase(self):
        """Currency code is normalized to uppercase."""
        exp = Exposure("test", "revenue", 100, "usd")
        assert exp.currency == "USD"

    def test_invalid_exp_type_raises(self):
        """Invalid exposure type raises ValueError."""
        with pytest.raises(ValueError, match="revenue.*cost"):
            Exposure("test", "invalid", 100, "USD")

    def test_zero_amount_raises(self):
        """Zero amount raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Exposure("test", "revenue", 0, "USD")

    def test_negative_amount_raises(self):
        """Negative amount raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Exposure("test", "cost", -100, "USD")

    def test_invalid_currency_length_raises(self):
        """Invalid currency code length raises ValueError."""
        with pytest.raises(ValueError, match="3-letter"):
            Exposure("test", "revenue", 100, "US")

    def test_empty_name_raises(self):
        """Empty name raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            Exposure("", "revenue", 100, "USD")

    def test_convert_to_base_foreign(self):
        """Convert foreign currency exposure to base."""
        exp = Exposure("test", "revenue", 1000, "USD")
        rates = {"USD": 0.92}
        assert exp.convert_to_base(rates, "EUR") == 920.0

    def test_convert_to_base_same_currency(self):
        """Base currency exposure converts at 1.0."""
        exp = Exposure("test", "revenue", 1000, "EUR")
        rates = {"USD": 0.92}
        assert exp.convert_to_base(rates, "EUR") == 1000.0

    def test_convert_to_base_missing_rate_raises(self):
        """Missing FX rate raises KeyError."""
        exp = Exposure("test", "revenue", 1000, "CHF")
        rates = {"USD": 0.92}
        with pytest.raises(KeyError, match="CHF"):
            exp.convert_to_base(rates, "EUR")

    def test_to_dict(self):
        """Serialization to dict."""
        exp = Exposure("test", "revenue", 1000, "USD")
        d = exp.to_dict()
        assert d["name"] == "test"
        assert d["exp_type"] == "revenue"
        assert d["amount"] == 1000
        assert d["currency"] == "USD"
        assert "created_at" in d

    def test_repr(self):
        """String representation."""
        exp = Exposure("test", "revenue", 1000, "USD")
        assert "test" in repr(exp)
        assert "revenue" in repr(exp)


# ── CompanyFXProfile Tests ────────────────────────────────────────────

class TestCompanyFXProfile:
    """Tests for the CompanyFXProfile dataclass."""

    def _sample_profile(self) -> CompanyFXProfile:
        """Create a sample profile for testing."""
        return CompanyFXProfile(
            company_name="TestCo",
            base_currency="EUR",
            exposures=[
                Exposure("US_Sales", "revenue", 500000, "USD"),
                Exposure("UK_Sales", "revenue", 200000, "GBP"),
                Exposure("EU_Ops", "cost", 300000, "EUR"),
                Exposure("JP_Parts", "cost", 10000000, "JPY"),
            ],
        )

    def test_create_profile(self):
        """Create a valid profile."""
        profile = self._sample_profile()
        assert profile.company_name == "TestCo"
        assert profile.base_currency == "EUR"
        assert len(profile.exposures) == 4

    def test_empty_company_name_raises(self):
        """Empty company name raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            CompanyFXProfile("", "EUR")

    def test_invalid_base_currency_raises(self):
        """Invalid base currency raises ValueError."""
        with pytest.raises(ValueError, match="3-letter"):
            CompanyFXProfile("TestCo", "EU")

    def test_add_exposure(self):
        """Add a single exposure."""
        profile = CompanyFXProfile("TestCo", "EUR")
        exp = Exposure("test", "revenue", 1000, "USD")
        profile.add_exposure(exp)
        assert len(profile.exposures) == 1

    def test_add_exposure_invalid_type(self):
        """Adding non-Exposure raises TypeError."""
        profile = CompanyFXProfile("TestCo", "EUR")
        with pytest.raises(TypeError):
            profile.add_exposure({"name": "test"})

    def test_currencies_property(self):
        """Get unique foreign currencies."""
        profile = self._sample_profile()
        currencies = sorted(profile.currencies)
        assert "USD" in currencies
        assert "GBP" in currencies
        assert "JPY" in currencies
        assert "EUR" not in currencies  # base currency excluded

    def test_revenue_exposures(self):
        """Filter revenue exposures."""
        profile = self._sample_profile()
        revenues = profile.total_revenue_exposures
        assert len(revenues) == 2
        assert all(e.exp_type == "revenue" for e in revenues)

    def test_cost_exposures(self):
        """Filter cost exposures."""
        profile = self._sample_profile()
        costs = profile.total_cost_exposures
        assert len(costs) == 2
        assert all(e.exp_type == "cost" for e in costs)

    def test_net_exposure_by_currency(self):
        """Calculate net exposure by currency."""
        profile = self._sample_profile()
        rates = {"USD": 0.92, "GBP": 1.15, "JPY": 0.0062}
        net = profile.net_exposure_by_currency(rates)
        assert "USD" in net
        assert net["USD"] > 0  # Revenue
        assert net["JPY"] < 0  # Cost

    def test_summary(self):
        """Profile summary includes expected fields."""
        profile = self._sample_profile()
        rates = {"USD": 0.92, "GBP": 1.15, "JPY": 0.0062}
        summary = profile.summary(rates)
        assert summary["company_name"] == "TestCo"
        assert summary["num_exposures"] == 4
        assert "total_revenue" in summary
        assert "total_cost" in summary
        assert "net_profit" in summary

    def test_to_dict(self):
        """Serialization to dict."""
        profile = self._sample_profile()
        d = profile.to_dict()
        assert d["company_name"] == "TestCo"
        assert len(d["exposures"]) == 4
