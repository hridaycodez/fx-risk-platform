"""
Tests for API routes using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_exposures_payload():
    """Sample payload for uploading exposures."""
    return {
        "company_name": "TestCo",
        "base_currency": "EUR",
        "exposures": [
            {"name": "US_Sales", "exp_type": "revenue", "amount": 500000, "currency": "USD"},
            {"name": "UK_Sales", "exp_type": "revenue", "amount": 200000, "currency": "GBP"},
            {"name": "EU_Ops", "exp_type": "cost", "amount": 300000, "currency": "EUR"},
            {"name": "JP_Parts", "exp_type": "cost", "amount": 10000000, "currency": "JPY"},
        ],
    }


# ── Health Check ──────────────────────────────────────────────────────

class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_check(self, client):
        """Health endpoint returns 200."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Root endpoint returns API info."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "FX Risk Engine API"


# ── Exposures ─────────────────────────────────────────────────────────

class TestExposuresEndpoint:
    """Tests for /exposures endpoints."""

    def test_upload_exposures(self, client, sample_exposures_payload):
        """POST /exposures creates a profile."""
        resp = client.post("/exposures", json=sample_exposures_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "created"
        assert data["company_name"] == "TestCo"
        assert data["num_exposures"] == 4
        assert "profile_id" in data

    def test_upload_invalid_exposure_type(self, client):
        """POST /exposures with invalid exp_type returns 422."""
        payload = {
            "company_name": "Bad",
            "exposures": [
                {"name": "test", "exp_type": "invalid", "amount": 100, "currency": "USD"}
            ],
        }
        resp = client.post("/exposures", json=payload)
        assert resp.status_code == 422

    def test_upload_zero_amount(self, client):
        """POST /exposures with zero amount returns 422."""
        payload = {
            "company_name": "Bad",
            "exposures": [
                {"name": "test", "exp_type": "revenue", "amount": 0, "currency": "USD"}
            ],
        }
        resp = client.post("/exposures", json=payload)
        assert resp.status_code == 422

    def test_list_profiles(self, client, sample_exposures_payload):
        """GET /exposures lists stored profiles."""
        client.post("/exposures", json=sample_exposures_payload)
        resp = client.get("/exposures")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_nonexistent_profile(self, client):
        """GET /exposures/{id} returns 404 for missing profile."""
        resp = client.get("/exposures/nonexistent")
        assert resp.status_code == 404


# ── Scenarios ─────────────────────────────────────────────────────────

class TestScenariosEndpoint:
    """Tests for /scenarios endpoints."""

    def test_list_predefined_scenarios(self, client):
        """GET /scenarios includes predefined scenarios."""
        resp = client.get("/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5  # predefined scenarios

    def test_create_scenario(self, client):
        """POST /scenarios creates a custom scenario."""
        payload = {
            "name": "Custom_Test",
            "shock_percentages": {"USD": -0.10, "GBP": 0.05},
            "description": "Test custom scenario",
        }
        resp = client.post("/scenarios", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Custom_Test"

    def test_get_scenario(self, client):
        """GET /scenarios/{name} returns scenario details."""
        resp = client.get("/scenarios/USD_Crash")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "USD_Crash"

    def test_get_nonexistent_scenario(self, client):
        """GET /scenarios/{name} returns 404 for missing scenario."""
        resp = client.get("/scenarios/NonExistent")
        assert resp.status_code == 404


# ── Analytics ─────────────────────────────────────────────────────────

class TestAnalyticsEndpoints:
    """Tests for /run_pnl, /run_sensitivity, /run_montecarlo endpoints."""

    def _inline_exposures(self):
        """Inline exposures for analytics requests."""
        return [
            {"name": "US_Sales", "exp_type": "revenue", "amount": 500000, "currency": "USD"},
            {"name": "JP_Parts", "exp_type": "cost", "amount": 10000000, "currency": "JPY"},
        ]

    def test_run_pnl(self, client):
        """POST /run_pnl returns P&L results."""
        resp = client.post("/run_pnl", json={
            "exposures": self._inline_exposures(),
            "base_currency": "EUR",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "profit" in data
        assert "total_revenue" in data
        assert "total_cost" in data
        assert "margin" in data

    def test_run_pnl_with_scenario(self, client):
        """POST /run_pnl with a named scenario."""
        resp = client.post("/run_pnl", json={
            "exposures": self._inline_exposures(),
            "base_currency": "EUR",
            "scenario_name": "USD_Crash",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["profit"] != 0

    def test_run_pnl_missing_exposures(self, client):
        """POST /run_pnl without exposures returns 422."""
        resp = client.post("/run_pnl", json={"base_currency": "EUR"})
        assert resp.status_code == 422

    def test_run_sensitivity(self, client):
        """POST /run_sensitivity returns sensitivity curve."""
        resp = client.post("/run_sensitivity", json={
            "exposures": self._inline_exposures(),
            "target_currency": "USD",
            "base_currency": "EUR",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_currency"] == "USD"
        assert len(data["results"]) > 0
        assert "summary" in data

    def test_run_montecarlo(self, client):
        """POST /run_montecarlo returns risk metrics."""
        resp = client.post("/run_montecarlo", json={
            "exposures": self._inline_exposures(),
            "base_currency": "EUR",
            "iterations": 200,
            "seed": 42,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["iterations"] == 200
        assert "risk_metrics" in data
        assert "var_95" in data["risk_metrics"]
        assert "cvar_95" in data["risk_metrics"]
        assert "profit_percentiles" in data

    def test_run_montecarlo_with_profile(self, client, sample_exposures_payload):
        """POST /run_montecarlo using a stored profile."""
        # First upload profile
        upload_resp = client.post("/exposures", json=sample_exposures_payload)
        profile_id = upload_resp.json()["profile_id"]

        # Then run Monte Carlo
        resp = client.post("/run_montecarlo", json={
            "profile_id": profile_id,
            "iterations": 100,
            "seed": 42,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_metrics" in data
