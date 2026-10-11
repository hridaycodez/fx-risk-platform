"""
FX Risk Engine — Core Analytics Package
========================================

A modular foreign exchange risk simulation and analytics engine.
Provides PnL computation, sensitivity analysis, Monte Carlo simulation,
and statistical risk metrics (VaR, CVaR, downside probability).

Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "FX Risk Engine Team"

from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.models.profile import CompanyFXProfile
from fx_risk_engine.models.scenario import FXScenario

__all__ = [
    "Exposure",
    "CompanyFXProfile",
    "FXScenario",
]
