from dataclasses import dataclass

@dataclass
class Exposure:
    """
    Represents a single FX exposure for a company.
    Type: revenue / cost
    """
    name: str
    exp_type: str  # 'revenue' or 'cost'
    amount: float
    currency: str

    def __post_init__(self):
        """Basic validation."""
        if self.exp_type not in ['revenue', 'cost']:
            raise ValueError(f"Exposure type must be 'revenue' or 'cost', got '{self.exp_type}'")
        if self.amount <= 0:
            raise ValueError("Exposure amount must be positive.")
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter string (e.g., 'USD').")

    def __repr__(self):
        return f"Exposure(name='{self.name}', type='{self.exp_type}', amount={self.amount:,.2f} {self.currency})"
