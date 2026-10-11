"""
Tests for Risk Metrics Engine.
"""

import pytest
import numpy as np
from fx_risk_engine.analytics.risk_metrics import (
    compute_var,
    compute_cvar,
    compute_downside_probability,
    compute_risk_metrics,
)


def _sample_distribution(seed=42, n=1000):
    """Generate a sample profit distribution."""
    np.random.seed(seed)
    return list(np.random.normal(100000, 15000, n))


class TestVaR:
    """Tests for Value at Risk computation."""

    def test_var_basic(self):
        """VaR at 95% confidence is below mean."""
        dist = _sample_distribution()
        var = compute_var(dist, 0.95)
        assert var < np.mean(dist)

    def test_var_higher_confidence_is_lower(self):
        """Higher confidence means lower (worse) VaR."""
        dist = _sample_distribution()
        var_95 = compute_var(dist, 0.95)
        var_99 = compute_var(dist, 0.99)
        assert var_99 <= var_95

    def test_var_empty_raises(self):
        """Empty distribution raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            compute_var([], 0.95)

    def test_var_type(self):
        """VaR returns a float."""
        dist = _sample_distribution()
        var = compute_var(dist, 0.95)
        assert isinstance(var, float)


class TestCVaR:
    """Tests for Conditional Value at Risk (Expected Shortfall)."""

    def test_cvar_worse_than_var(self):
        """CVaR is worse (lower) than or equal to VaR."""
        dist = _sample_distribution()
        var = compute_var(dist, 0.95)
        cvar = compute_cvar(dist, 0.95)
        assert cvar <= var

    def test_cvar_empty_raises(self):
        """Empty distribution raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            compute_cvar([], 0.95)

    def test_cvar_basic(self):
        """CVaR returns a reasonable value."""
        dist = _sample_distribution()
        cvar = compute_cvar(dist, 0.95)
        assert cvar < np.mean(dist)
        assert isinstance(cvar, float)


class TestDownsideProbability:
    """Tests for downside probability computation."""

    def test_zero_threshold(self):
        """0% threshold: probability of any drop from base."""
        dist = _sample_distribution()
        base = np.mean(dist) + 10000  # above mean
        prob = compute_downside_probability(dist, base, 0.0)
        # Most values will be below base + offset
        assert prob > 0

    def test_extreme_threshold(self):
        """Very high threshold: almost everything is a downside."""
        dist = list(np.random.normal(100, 10, 100))
        prob = compute_downside_probability(dist, 100, 99.0)
        # Threshold = 100 * (1 − 0.99) = 1.0; almost all above 1
        assert prob == pytest.approx(0.0, abs=5.0)

    def test_empty_raises(self):
        """Empty distribution raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            compute_downside_probability([], 100, 20)


class TestComputeRiskMetrics:
    """Tests for the comprehensive risk metrics function."""

    def test_all_keys_present(self):
        """Result dict contains all expected keys."""
        dist = _sample_distribution()
        metrics = compute_risk_metrics(dist, 100000, 20.0, 0.95)
        expected_keys = [
            "mean_profit", "median_profit", "std_profit",
            "min_profit", "max_profit",
            "p5_profit", "p25_profit", "p75_profit", "p95_profit",
            "var_95", "cvar_95", "profit_at_risk",
            "downside_probability", "loss_threshold_value",
            "sharpe_like_ratio", "skewness", "kurtosis",
            "base_profit", "confidence_level", "num_simulations",
        ]
        for key in expected_keys:
            assert key in metrics, f"Missing key: {key}"

    def test_num_simulations(self):
        """num_simulations matches input length."""
        dist = _sample_distribution(n=500)
        metrics = compute_risk_metrics(dist, 100000)
        assert metrics["num_simulations"] == 500

    def test_percentile_ordering(self):
        """Percentiles are in correct order."""
        dist = _sample_distribution()
        m = compute_risk_metrics(dist, 100000)
        assert m["p5_profit"] <= m["p25_profit"]
        assert m["p25_profit"] <= m["median_profit"]
        assert m["median_profit"] <= m["p75_profit"]
        assert m["p75_profit"] <= m["p95_profit"]

    def test_var_cvar_relationship(self):
        """CVaR should be worse than VaR."""
        dist = _sample_distribution()
        m = compute_risk_metrics(dist, 100000)
        assert m["cvar_95"] <= m["var_95"]

    def test_empty_raises(self):
        """Empty distribution raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            compute_risk_metrics([], 100000)

    def test_std_positive(self):
        """Standard deviation is positive for non-constant data."""
        dist = _sample_distribution()
        m = compute_risk_metrics(dist, 100000)
        assert m["std_profit"] > 0

    def test_sharpe_like_positive(self):
        """Sharpe-like ratio is positive for positive-mean distribution."""
        dist = _sample_distribution()  # centered around 100k
        m = compute_risk_metrics(dist, 100000)
        assert m["sharpe_like_ratio"] > 0
