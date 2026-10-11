"""
Company FX Profile Model
=========================

Aggregates a company's FX exposures under a single entity
with a base/reporting currency.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any

from fx_risk_engine.models.exposure import Exposure


@dataclass
class CompanyFXProfile:
    """
    Represents a company's complete FX exposure profile.

    Attributes:
        company_name: Name of the company.
        base_currency: The company's reporting / functional currency (e.g., 'EUR').
        exposures: List of individual FX exposures.
        created_at: Timestamp of profile creation.
    """

    company_name: str
    base_currency: str
    exposures: List[Exposure] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        """Validate profile fields."""
        if not self.company_name:
            raise ValueError("Company name must be a non-empty string.")
        if not isinstance(self.base_currency, str) or len(self.base_currency) != 3:
            raise ValueError("Base currency must be a 3-letter ISO 4217 code.")
        self.base_currency = self.base_currency.upper()

    def add_exposure(self, exposure: Exposure) -> None:
        """Add a single exposure to the profile."""
        if not isinstance(exposure, Exposure):
            raise TypeError("Expected an Exposure instance.")
        self.exposures.append(exposure)

    def add_exposures(self, exposures: List[Exposure]) -> None:
        """Add multiple exposures to the profile."""
        for exp in exposures:
            self.add_exposure(exp)

    @property
    def currencies(self) -> List[str]:
        """Return unique list of foreign currencies in this profile."""
        return list({
            exp.currency
            for exp in self.exposures
            if exp.currency != self.base_currency
        })

    @property
    def total_revenue_exposures(self) -> List[Exposure]:
        """Return all revenue exposures."""
        return [e for e in self.exposures if e.exp_type == "revenue"]

    @property
    def total_cost_exposures(self) -> List[Exposure]:
        """Return all cost exposures."""
        return [e for e in self.exposures if e.exp_type == "cost"]

    def net_exposure_by_currency(
        self, fx_rates: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate net exposure per currency in base currency terms.

        Args:
            fx_rates: FX rates dict (currency -> rate in base currency).

        Returns:
            Dict mapping each currency to its net exposure in base currency.
        """
        net: Dict[str, float] = {}
        for exp in self.exposures:
            base_amount = exp.convert_to_base(fx_rates, self.base_currency)
            signed = base_amount * exp.sign
            net[exp.currency] = net.get(exp.currency, 0.0) + signed
        return net

    def summary(self, fx_rates: Dict[str, float]) -> Dict[str, Any]:
        """Return a high-level summary of the profile."""
        net_by_ccy = self.net_exposure_by_currency(fx_rates)
        total_revenue = sum(
            exp.convert_to_base(fx_rates, self.base_currency)
            for exp in self.total_revenue_exposures
        )
        total_cost = sum(
            exp.convert_to_base(fx_rates, self.base_currency)
            for exp in self.total_cost_exposures
        )
        return {
            "company_name": self.company_name,
            "base_currency": self.base_currency,
            "num_exposures": len(self.exposures),
            "foreign_currencies": self.currencies,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "net_profit": total_revenue - total_cost,
            "net_exposure_by_currency": net_by_ccy,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the profile to a dictionary."""
        return {
            "company_name": self.company_name,
            "base_currency": self.base_currency,
            "exposures": [e.to_dict() for e in self.exposures],
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return (
            f"CompanyFXProfile(company='{self.company_name}', "
            f"base='{self.base_currency}', exposures={len(self.exposures)})"
        )
