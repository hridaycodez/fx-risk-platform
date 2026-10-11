"""
live_rates.py — Live FX Rate Fetcher
======================================
Fetches real-time FX rates from the Frankfurter API (free, no API key).
Falls back to config.py hardcoded rates if the API is unreachable.
Results are cached in-memory for 30 seconds.

Frankfurter API docs: https://www.frankfurter.app/docs/
"""

import time
import logging
import requests
from typing import Dict, Optional

import config

logger = logging.getLogger("fx_risk_engine.live_rates")

# ── Simple in-memory cache ────────────────────────────────────────────────────
_cache: Dict = {}
_CACHE_TTL = 30  # seconds


def _is_cached(key: str) -> bool:
    if key not in _cache:
        return False
    return time.time() - _cache[key]["timestamp"] < _CACHE_TTL


def get_live_rates(base: str = "EUR") -> Dict[str, float]:
    """
    Returns live FX rates from Frankfurter API with fallback to config.py defaults.
    Result is cached for 30 seconds.

    Returns:
        dict: { "USD": 1.08, "GBP": 0.856, "INR": 90.42, "AED": 3.97, "JPY": 161.3, "CHF": 0.962 }
    """
    cache_key = f"rates_{base}"

    if _is_cached(cache_key):
        logger.debug("Returning cached FX rates")
        return _cache[cache_key]["data"]

    symbols = ",".join(config.SUPPORTED_CURRENCIES)
    url = f"https://api.frankfurter.app/latest?base={base}&to={symbols}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        rates = response.json()["rates"]

        # Ensure all 6 currencies are present (fallback individual missing ones)
        for ccy in config.SUPPORTED_CURRENCIES:
            if ccy not in rates:
                logger.warning("Missing %s from live rates — using fallback", ccy)
                rates[ccy] = config.BASE_FX_RATES.get(ccy, 1.0)

        _cache[cache_key] = {"data": rates, "timestamp": time.time()}
        logger.info("✅ Live FX rates fetched from Frankfurter API")
        return rates

    except (requests.RequestException, KeyError, ValueError) as err:
        logger.warning("⚠️  Frankfurter API failed (%s) — using fallback rates", err)
        fallback = dict(config.BASE_FX_RATES)
        _cache[cache_key] = {"data": fallback, "timestamp": time.time()}
        return fallback


def get_historical_rates(base: str, to: str, start_date: str, end_date: str) -> Dict:
    """
    Fetch historical daily rates for a currency pair.
    Used by ML training data preparation.

    Args:
        base: base currency (e.g. "EUR")
        to:   target currency (e.g. "INR")
        start_date: "YYYY-MM-DD"
        end_date:   "YYYY-MM-DD"
    """
    url = f"https://api.frankfurter.app/{start_date}..{end_date}?base={base}&to={to}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as err:
        raise RuntimeError(f"Historical rate fetch failed: {err}") from err
