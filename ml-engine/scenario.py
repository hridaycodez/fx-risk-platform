from dataclasses import dataclass
from typing import Dict

@dataclass
class FXScenario:
    """
    Represents a foreign exchange (FX) shock scenario.
    """
    name: str
    shock_percentages: Dict[str, float]  # e.g., {"USD": 0.10, "EUR": -0.05}

    def apply_shock(self, base_fx_rates: Dict[str, float]) -> Dict[str, float]:
        """
        Applies the defined shock percentages to a set of base FX rates.

        Args:
            base_fx_rates: A dictionary of base FX rates, where keys are currency codes
                           and values are the exchange rates against the base currency.

        Returns:
            A new dictionary with the shocked FX rates.
        """
        shocked_rates = base_fx_rates.copy()
        for currency, shock in self.shock_percentages.items():
            if currency in shocked_rates:
                shocked_rates[currency] *= (1 + shock)
        return shocked_rates
