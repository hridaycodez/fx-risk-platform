"""
FX Scenario Model
=================

Represents a foreign exchange shock scenario with audit metadata.
Supports named scenarios, descriptions, and timestamped creation
for auditability.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional


@dataclass
class FXScenario:
    """
    Represents a foreign exchange shock scenario.

    Attributes:
        name: Unique scenario identifier (e.g., 'USD_Crash').
        shock_percentages: Currency -> shock as a decimal
                           (e.g., {'USD': -0.15} means USD weakens 15%).
        description: Human-readable description of the scenario.
        created_at: ISO timestamp of scenario creation.
        created_by: Author or system that created the scenario.
    """

    name: str
    shock_percentages: Dict[str, float]
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = "system"

    def __post_init__(self) -> None:
        """Validate scenario fields."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Scenario name must be a non-empty string.")
        if not isinstance(self.shock_percentages, dict) or not self.shock_percentages:
            raise ValueError("Shock percentages must be a non-empty dictionary.")
        # Validate shock values
        for ccy, shock in self.shock_percentages.items():
            if not isinstance(ccy, str) or len(ccy) != 3:
                raise ValueError(f"Currency '{ccy}' must be a 3-letter code.")
            if not isinstance(shock, (int, float)):
                raise ValueError(
                    f"Shock for '{ccy}' must be numeric, got {type(shock).__name__}."
                )

    def apply_shock(self, base_fx_rates: Dict[str, float]) -> Dict[str, float]:
        """
        Apply the defined shock percentages to base FX rates.

        Args:
            base_fx_rates: Dict of currency -> base FX rate.

        Returns:
            New dict with shocked FX rates. Currencies not in
            shock_percentages are unchanged.
        """
        shocked_rates = base_fx_rates.copy()
        for currency, shock in self.shock_percentages.items():
            if currency in shocked_rates:
                shocked_rates[currency] *= (1 + shock)
        return shocked_rates

    def impact_summary(
        self, base_fx_rates: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Summarize the rate changes for each shocked currency.

        Returns:
            Dict of currency -> {base_rate, shocked_rate, change_pct}.
        """
        shocked = self.apply_shock(base_fx_rates)
        summary: Dict[str, Dict[str, float]] = {}
        for ccy, shock in self.shock_percentages.items():
            if ccy in base_fx_rates:
                summary[ccy] = {
                    "base_rate": base_fx_rates[ccy],
                    "shocked_rate": shocked[ccy],
                    "change_pct": shock * 100,
                }
        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Serialize scenario to a dictionary."""
        return {
            "name": self.name,
            "shock_percentages": self.shock_percentages,
            "description": self.description,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FXScenario":
        """Deserialize a scenario from a dictionary."""
        return cls(
            name=data["name"],
            shock_percentages=data["shock_percentages"],
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by", "system"),
        )

    def __repr__(self) -> str:
        shocks = ", ".join(
            f"{k}: {v:+.1%}" for k, v in self.shock_percentages.items()
        )
        return f"FXScenario(name='{self.name}', shocks={{{shocks}}})"
