"""
predict.py — ML Inference Module (Runtime)
============================================
Loads pre-trained models from trained_models/ and exposes prediction functions.
All predictions run in < 50ms. No training happens here.
"""

import os
import logging
import numpy as np
import joblib
from typing import Dict, Optional

logger = logging.getLogger("fx_risk_engine.ml.predict")

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trained_models")

# ── Lazy-loaded model cache ───────────────────────────────────────────────────
_models: Dict = {}


def _load_model(name: str):
    """Load a model from disk, with caching."""
    if name not in _models:
        path = os.path.join(MODELS_DIR, f"{name}.joblib")
        if not os.path.exists(path):
            logger.warning("Model file not found: %s — using fallback logic", path)
            return None
        _models[name] = joblib.load(path)
        logger.info("✅ Loaded ML model: %s", name)
    return _models[name]


def predict_risk_level(
    downside_probability: float,
    var_95: float,
    mean_profit: float,
    std_profit: float,
) -> Dict:
    """
    Predict risk classification (LOW / MEDIUM / HIGH) using the trained Random Forest.
    Falls back to rule-based classification if model file is missing.

    Returns:
        {
            "risk_level": "HIGH",
            "confidence": 0.87,
            "probabilities": {"LOW": 0.05, "MEDIUM": 0.08, "HIGH": 0.87}
        }
    """
    clf = _load_model("risk_classifier")

    if abs(mean_profit) < 1e-6:
        loss_ratio = 1.0 if var_95 < 0 else 0.5
        portfolio_vol = 0.5
        sharpe = 0.0
    elif var_95 < 0:
        loss_ratio = 1.0 + (abs(var_95) / abs(mean_profit))
        portfolio_vol = abs(std_profit / mean_profit)
        sharpe = mean_profit / std_profit if std_profit > 0 else 0.0
    else:
        loss_ratio = max(0.0, (mean_profit - var_95) / mean_profit)
        portfolio_vol = abs(std_profit / mean_profit)
        sharpe = mean_profit / std_profit if std_profit > 0 else 0.0

    features = np.array([[downside_probability, loss_ratio, portfolio_vol, sharpe]])

    if clf is None:
        # Fallback rule-based
        if var_95 < 0 or downside_probability > 30 or loss_ratio > 0.5:
            level = "HIGH"
        elif downside_probability > 15 or loss_ratio > 0.25:
            level = "MEDIUM"
        else:
            level = "LOW"
        return {"risk_level": level, "confidence": 0.7, "probabilities": {}, "model": "rule-based"}

    prediction = clf.predict(features)[0]
    proba = clf.predict_proba(features)[0]
    classes = clf.classes_

    probabilities = {cls: round(float(p), 4) for cls, p in zip(classes, proba)}
    confidence = round(float(max(proba)), 4)

    return {
        "risk_level": prediction,
        "confidence": confidence,
        "probabilities": probabilities,
        "model": "random-forest",
    }


def get_volatility_forecast(currency: str) -> Optional[Dict]:
    """
    Get the EWMA-based volatility forecast for a currency.
    Returns current estimated annual and daily volatility.

    Returns:
        {
            "currency": "INR",
            "annual_volatility": 0.0452,
            "daily_volatility": 0.00285,
            "model": "ewma"
        }
    """
    vol_models = _load_model("volatility_model")
    if vol_models is None or currency not in vol_models:
        return None

    model = vol_models[currency]
    return {
        "currency": currency,
        "annual_volatility": model["current_annual_vol"],
        "daily_volatility": model["current_daily_vol"],
        "ewma_lambda": model["ewma_lambda"],
        "model": "ewma",
    }


def get_all_volatility_forecasts() -> Dict:
    """Get volatility forecasts for all supported currencies."""
    vol_models = _load_model("volatility_model")
    if vol_models is None:
        return {}
    
    result = {}
    for ccy, model in vol_models.items():
        result[ccy] = {
            "annual_volatility": model["current_annual_vol"],
            "daily_volatility": model["current_daily_vol"],
        }
    return result
