"""
Risk Classifier (Scaffold)
============================

Placeholder module for ML-based downside risk classification.
In production, this would use a trained supervised model (e.g.,
Random Forest, XGBoost) to classify whether a given FX exposure
profile is at high, medium, or low risk of significant loss.

Current implementation uses simple heuristic rules.
"""

import logging
from typing import List, Dict, Any, Optional

from fx_risk_engine.models.exposure import Exposure

logger = logging.getLogger(__name__)


# Risk thresholds
_HIGH_CONCENTRATION_THRESHOLD = 0.60  # 60% in single currency
_HIGH_VOLATILITY_THRESHOLD = 0.08     # 8% vol
_LARGE_EXPOSURE_THRESHOLD = 1_000_000  # 1M base currency units


def classify_risk(
    exposures: List[Exposure],
    fx_rates: Dict[str, float],
    volatilities: Dict[str, float],
    base_currency: str = "EUR",
) -> Dict[str, Any]:
    """
    Classify the risk level of a portfolio.

    **Scaffold**: Uses rule-based heuristics. In production, this
    would use a trained ML classifier.

    Args:
        exposures: List of FX exposures.
        fx_rates: Current FX rates.
        volatilities: FX volatilities per currency.
        base_currency: The base currency.

    Returns:
        Dict with risk_level ('low', 'medium', 'high'),
        risk_score (0-100), and contributing factors.

    TODO:
        - Train Random Forest on historical portfolio outcomes
        - Feature engineering: concentration, vol, correlation, size
        - Implement cross-validation and model selection
        - Add probability estimates (predict_proba)
        - Support online learning / model updates
    """
    factors: List[str] = []
    risk_score = 0

    # Factor 1: Currency concentration
    total_base = 0.0
    by_currency: Dict[str, float] = {}
    for exp in exposures:
        if exp.currency == base_currency:
            amount = exp.amount
        else:
            rate = fx_rates.get(exp.currency, 1.0)
            amount = exp.amount * rate
        total_base += amount
        by_currency[exp.currency] = by_currency.get(exp.currency, 0.0) + amount

    if total_base > 0:
        for ccy, amt in by_currency.items():
            if ccy != base_currency:
                concentration = amt / total_base
                if concentration > _HIGH_CONCENTRATION_THRESHOLD:
                    risk_score += 30
                    factors.append(
                        f"High concentration in {ccy} ({concentration:.0%})"
                    )

    # Factor 2: High-volatility currencies
    for exp in exposures:
        vol = volatilities.get(exp.currency, 0.05)
        if vol > _HIGH_VOLATILITY_THRESHOLD:
            risk_score += 15
            factors.append(f"{exp.currency} has high volatility ({vol:.1%})")

    # Factor 3: Large absolute exposure
    if total_base > _LARGE_EXPOSURE_THRESHOLD:
        risk_score += 20
        factors.append(f"Large total exposure ({total_base:,.0f} {base_currency})")

    # Factor 4: Unhedged mismatch (revenues vs costs in same currency)
    revenue_ccys = {e.currency for e in exposures if e.exp_type == "revenue"}
    cost_ccys = {e.currency for e in exposures if e.exp_type == "cost"}
    unhedged = (revenue_ccys | cost_ccys) - {base_currency}
    truly_unhedged = unhedged - (revenue_ccys & cost_ccys)  # no natural hedge
    if truly_unhedged:
        risk_score += 10 * len(truly_unhedged)
        factors.append(f"Unhedged currencies: {', '.join(truly_unhedged)}")

    # Clamp score
    risk_score = min(risk_score, 100)

    # Classify
    if risk_score >= 60:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    result = {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "factors": factors,
        "model": "heuristic_v1",
        "note": "Scaffold implementation. Production model not yet trained.",
    }

    logger.info("Risk classification: %s (score=%d)", risk_level, risk_score)
    return result
