# FX Risk Engine Configuration — 7 Currencies (EUR base)
# Updated for production platform with INR, AED, JPY, CHF support

import os
from dotenv import load_dotenv

load_dotenv()

# ── Base Currency ─────────────────────────────────────────────────────────────
BASE_CURRENCY = os.getenv("BASE_CURRENCY", "EUR")

# ── Supported Currencies ──────────────────────────────────────────────────────
SUPPORTED_CURRENCIES = ["USD", "GBP", "INR", "AED", "JPY", "CHF"]

# ── Currency Metadata (for API responses) ─────────────────────────────────────
CURRENCY_META = {
    "EUR": {"name": "Euro",          "flag": "🇪🇺", "symbol": "€",    "region": "Eurozone"},
    "USD": {"name": "US Dollar",     "flag": "🇺🇸", "symbol": "$",    "region": "United States"},
    "GBP": {"name": "British Pound", "flag": "🇬🇧", "symbol": "£",    "region": "United Kingdom"},
    "INR": {"name": "Indian Rupee",  "flag": "🇮🇳", "symbol": "₹",    "region": "India"},
    "AED": {"name": "UAE Dirham",    "flag": "🇦🇪", "symbol": "د.إ",  "region": "Dubai / UAE"},
    "JPY": {"name": "Japanese Yen",  "flag": "🇯🇵", "symbol": "¥",    "region": "Japan"},
    "CHF": {"name": "Swiss Franc",   "flag": "🇨🇭", "symbol": "Fr",   "region": "Switzerland", "safe_haven": True},
}

# ── Fallback FX Rates (EUR as base, used if live API is unreachable) ──────────
# These are approximate mid-market rates — updated periodically
BASE_FX_RATES = {
    "USD": float(os.getenv("FX_RATE_USD", 1.08)),    # 1 EUR = 1.08 USD
    "GBP": float(os.getenv("FX_RATE_GBP", 0.856)),   # 1 EUR = 0.856 GBP
    "INR": float(os.getenv("FX_RATE_INR", 90.42)),   # 1 EUR = 90.42 INR
    "AED": float(os.getenv("FX_RATE_AED", 3.97)),    # 1 EUR = 3.97 AED
    "JPY": float(os.getenv("FX_RATE_JPY", 161.30)),  # 1 EUR = 161.30 JPY
    "CHF": float(os.getenv("FX_RATE_CHF", 0.962)),   # 1 EUR = 0.962 CHF
}

# ── FX Volatility (annualized standard deviation) ────────────────────────────
# Used as the per-step shock distribution in Monte Carlo simulation.
# Sources: historical realized volatility (approx values)
FX_VOLATILITY = {
    "USD": float(os.getenv("FX_VOL_USD", 0.050)),   # 5.0%  — major pair, liquid
    "GBP": float(os.getenv("FX_VOL_GBP", 0.070)),   # 7.0%  — Brexit/macro volatility
    "INR": float(os.getenv("FX_VOL_INR", 0.045)),   # 4.5%  — EM currency, RBI managed
    "AED": float(os.getenv("FX_VOL_AED", 0.010)),   # 1.0%  — USD-pegged, very stable
    "JPY": float(os.getenv("FX_VOL_JPY", 0.030)),   # 3.0%  — safe haven flows
    "CHF": float(os.getenv("FX_VOL_CHF", 0.040)),   # 4.0%  — safe haven, SNB managed
}

# ── Cholesky Correlation Matrix ───────────────────────────────────────────────
# Captures real-world FX correlations for correlated Monte Carlo simulation.
# Order: USD, GBP, INR, AED, JPY, CHF
# Key correlations:
#   AED is near-perfectly correlated with USD (USD-peg)
#   CHF and JPY both strengthen in risk-off (negative correlation with USD)
#   INR weakens when USD strengthens (negative correlation)
import numpy as np

CORRELATION_MATRIX = np.array([
    #  USD    GBP    INR    AED    JPY    CHF
    [ 1.00,  0.55, -0.40,  0.98, -0.30, -0.45],  # USD
    [ 0.55,  1.00, -0.20,  0.53, -0.15, -0.30],  # GBP
    [-0.40, -0.20,  1.00, -0.38,  0.10,  0.15],  # INR
    [ 0.98,  0.53, -0.38,  1.00, -0.28, -0.43],  # AED
    [-0.30, -0.15,  0.10, -0.28,  1.00,  0.60],  # JPY
    [-0.45, -0.30,  0.15, -0.43,  0.60,  1.00],  # CHF
])

# Pre-compute Cholesky decomposition (used by correlated Monte Carlo)
CHOLESKY_MATRIX = np.linalg.cholesky(CORRELATION_MATRIX)

# ── Monte Carlo Settings ──────────────────────────────────────────────────────
MC_ITERATIONS     = int(os.getenv("MC_ITERATIONS", 5000))
MC_CHUNK_SIZE     = int(os.getenv("MC_CHUNK_SIZE", 500))   # results emitted per stream chunk
LOSS_THRESHOLD_PERCENT = float(os.getenv("LOSS_THRESHOLD_PERCENT", 20.0))
CONFIDENCE_LEVEL  = float(os.getenv("CONFIDENCE_LEVEL", 0.95))

# ── API Settings ──────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG    = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:4000,http://localhost:5173"
).split(",")
