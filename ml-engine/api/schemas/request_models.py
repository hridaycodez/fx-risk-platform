"""
API Request & Response Schemas
===============================

Pydantic v2 models for request validation and response serialization.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Exposure Schemas ──────────────────────────────────────────────────

class ExposureInput(BaseModel):
    """Schema for a single FX exposure."""
    name: str = Field(default="Exposure", description="Exposure identifier")
    exp_type: str = Field(default="revenue", description="'revenue' or 'cost'")
    amount: float = Field(..., gt=0, description="Notional amount (positive)")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 code")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "expType" in data and "exp_type" not in data:
                data["exp_type"] = data["expType"]
            if not data.get("name"):
                data["name"] = f"{data.get('currency', 'FX')}_{data.get('exp_type', 'exp')}"
        return data

    @field_validator("exp_type")
    @classmethod
    def validate_exp_type(cls, v: str) -> str:
        if v not in ("revenue", "cost"):
            raise ValueError("exp_type must be 'revenue' or 'cost'")
        return v

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        return v.upper()


class UploadExposuresRequest(BaseModel):
    """Request to upload a company's FX exposures."""
    company_name: str = Field(..., min_length=1)
    base_currency: str = Field(default="EUR", min_length=3, max_length=3)
    exposures: List[ExposureInput] = Field(..., min_length=1)

    @field_validator("base_currency")
    @classmethod
    def normalize_base(cls, v: str) -> str:
        return v.upper()


class ExposureResponse(BaseModel):
    """Response after uploading exposures."""
    status: str
    company_name: str
    base_currency: str
    num_exposures: int
    profile_id: str


# ── Scenario Schemas ──────────────────────────────────────────────────

class ScenarioInput(BaseModel):
    """Schema for creating a new FX scenario."""
    name: str = Field(..., min_length=1)
    shock_percentages: Dict[str, float] = Field(
        ..., description="Currency -> shock decimal (e.g., {'USD': -0.15})"
    )
    description: str = Field(default="")

    @field_validator("shock_percentages")
    @classmethod
    def validate_shocks(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise ValueError("At least one currency shock is required")
        return {k.upper(): val for k, val in v.items()}


class ScenarioResponse(BaseModel):
    """Response for a single scenario."""
    name: str
    shock_percentages: Dict[str, float]
    description: str
    created_at: str
    created_by: str


# ── Analytics Schemas ─────────────────────────────────────────────────

class RunPnLRequest(BaseModel):
    """Request for deterministic P&L computation."""
    profile_id: Optional[str] = Field(
        default=None, description="ID of stored profile. If None, use inline exposures."
    )
    exposures: Optional[List[ExposureInput]] = Field(default=None)
    base_currency: str = Field(default="EUR")
    fx_rates: Optional[Dict[str, float]] = Field(
        default=None, description="Override FX rates. Uses defaults if None."
    )
    scenario_name: Optional[str] = Field(
        default=None, description="Apply a named scenario's shocks."
    )


class RunSensitivityRequest(BaseModel):
    """Request for sensitivity analysis."""
    profile_id: Optional[str] = Field(default=None)
    exposures: Optional[List[ExposureInput]] = Field(default=None)
    base_currency: str = Field(default="EUR")
    target_currency: str = Field(..., min_length=3, max_length=3)
    fx_rates: Optional[Dict[str, float]] = Field(default=None)
    shock_range: Optional[List[float]] = Field(
        default=None,
        description="Custom shock range (decimals). Default: -0.20 to +0.20"
    )

    @field_validator("target_currency")
    @classmethod
    def normalize_target(cls, v: str) -> str:
        return v.upper()


class RunMonteCarloRequest(BaseModel):
    """Request for Monte Carlo simulation."""
    profile_id: Optional[str] = Field(default=None)
    exposures: Optional[List[ExposureInput]] = Field(default=None)
    base_currency: str = Field(default="EUR")
    fx_rates: Optional[Dict[str, float]] = Field(default=None)
    volatilities: Optional[Dict[str, float]] = Field(default=None)
    iterations: int = Field(default=1000, ge=100, le=50000)
    seed: Optional[int] = Field(default=None)
    loss_threshold_pct: float = Field(default=20.0, ge=0, le=100)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.999)


class PnLResponse(BaseModel):
    """P&L computation response."""
    total_revenue: float
    total_cost: float
    profit: float
    margin: float
    base_currency: str
    breakdown: Optional[List[Dict[str, Any]]] = None


class SensitivityResponse(BaseModel):
    """Sensitivity analysis response."""
    target_currency: str
    base_currency: str
    results: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None


class MonteCarloResponse(BaseModel):
    """Monte Carlo simulation response."""
    iterations: int
    base_currency: str
    risk_metrics: Dict[str, Any]
    profit_percentiles: Dict[str, float]
    distribution_sample: Optional[List[float]] = Field(
        default=None, description="First 100 profit values for charting"
    )


# ── General ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """System health check response."""
    status: str
    version: str
    engine_status: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str
    status_code: int
