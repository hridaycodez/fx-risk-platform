"""
Exposure Model
==============

Represents a single foreign exchange exposure for a company.
Each exposure has a name, type (revenue or cost), notional amount,
and the currency in which it is denominated.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any


@dataclass
class Exposure:
    """
    Represents a single FX exposure for a company.

    Attributes:
        name: Human-readable identifier for the exposure (e.g., 'US_Sales').
        exp_type: Either 'revenue' or 'cost'.
        amount: Notional amount in the exposure's currency. Must be positive.
        currency: ISO 4217 3-letter currency code (e.g., 'USD', 'EUR').
        created_at: Timestamp of creation (auto-generated).
    """

    name: str
    exp_type: str  # 'revenue' or 'cost'
    amount: float
    currency: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        """Validate exposure fields after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Exposure name must be a non-empty string.")
        if self.exp_type not in ("revenue", "cost"):
            raise ValueError(
                f"Exposure type must be 'revenue' or 'cost', got '{self.exp_type}'"
            )
        if not isinstance(self.amount, (int, float)) or self.amount <= 0:
            raise ValueError("Exposure amount must be a positive number.")
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise ValueError(
                "Currency must be a 3-letter ISO 4217 code (e.g., 'USD')."
            )
        # Normalize currency to uppercase
        self.currency = self.currency.upper()

    @property
    def sign(self) -> float:
        """Returns +1.0 for revenue and -1.0 for cost."""
        return 1.0 if self.exp_type == "revenue" else -1.0

    def convert_to_base(self, fx_rates: Dict[str, float], base_currency: str) -> float:
        """
        Convert exposure amount to base currency.

        Args:
            fx_rates: Dict mapping currency code -> exchange rate
                      (units of base currency per 1 unit of foreign currency).
            base_currency: The company's base/reporting currency.

        Returns:
            Amount in base currency.
        """
        if self.currency == base_currency:
            return self.amount
        rate = fx_rates.get(self.currency)
        if rate is None:
            raise KeyError(
                f"No FX rate found for currency '{self.currency}' in provided rates."
            )
        return self.amount * rate

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exposure to a dictionary."""
        return {
            "name": self.name,
            "exp_type": self.exp_type,
            "amount": self.amount,
            "currency": self.currency,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return (
            f"Exposure(name='{self.name}', type='{self.exp_type}', "
            f"amount={self.amount:,.2f} {self.currency})"
        )
