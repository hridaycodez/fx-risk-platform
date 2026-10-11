"""
Configuration Settings
======================

Loads configuration from environment variables and .env files.
Provides typed defaults for all engine settings.
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _load_env_file(env_path: str = ".env") -> None:
    """
    Simple .env file loader. Reads KEY=VALUE pairs and sets them
    as environment variables if not already set.
    """
    if not os.path.exists(env_path):
        logger.debug("No .env file found at %s", env_path)
        return

    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


class Settings:
    """
    Application settings loaded from environment variables.

    Attributes:
        BASE_CURRENCY: The company's reporting currency.
        BASE_FX_RATES: Default FX rates.
        FX_VOLATILITY: Default volatility assumptions per currency.
        MC_ITERATIONS: Default Monte Carlo iteration count.
        LOSS_THRESHOLD_PERCENT: Default downside threshold.
        API_HOST: Host to bind the API server.
        API_PORT: Port for the API server.
        DEBUG: Enable debug mode.
        LOG_LEVEL: Logging level.
    """

    def __init__(self, env_path: str = ".env") -> None:
        """Load settings from environment."""
        _load_env_file(env_path)

        # Engine settings
        self.BASE_CURRENCY: str = os.getenv("BASE_CURRENCY", "EUR")
        self.MC_ITERATIONS: int = int(os.getenv("MC_ITERATIONS", "1000"))
        self.LOSS_THRESHOLD_PERCENT: float = float(
            os.getenv("LOSS_THRESHOLD_PERCENT", "20.0")
        )
        self.CONFIDENCE_LEVEL: float = float(
            os.getenv("CONFIDENCE_LEVEL", "0.95")
        )

        # Default FX rates (can be overridden at runtime)
        self.BASE_FX_RATES: Dict[str, float] = {
            "USD": float(os.getenv("FX_RATE_USD", "0.92")),
            "GBP": float(os.getenv("FX_RATE_GBP", "1.15")),
            "JPY": float(os.getenv("FX_RATE_JPY", "0.0062")),
        }

        # Default volatilities
        self.FX_VOLATILITY: Dict[str, float] = {
            "USD": float(os.getenv("FX_VOL_USD", "0.05")),
            "GBP": float(os.getenv("FX_VOL_GBP", "0.07")),
            "JPY": float(os.getenv("FX_VOL_JPY", "0.03")),
        }

        # API settings
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

        # CORS
        self.CORS_ORIGINS: list = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
        ).split(",")

    def to_dict(self) -> Dict:
        """Serialize settings to a dictionary (excluding sensitive data)."""
        return {
            "base_currency": self.BASE_CURRENCY,
            "mc_iterations": self.MC_ITERATIONS,
            "loss_threshold_pct": self.LOSS_THRESHOLD_PERCENT,
            "confidence_level": self.CONFIDENCE_LEVEL,
            "api_host": self.API_HOST,
            "api_port": self.API_PORT,
            "debug": self.DEBUG,
            "log_level": self.LOG_LEVEL,
        }


# Singleton instance
_settings: Optional[Settings] = None


def get_settings(env_path: str = ".env") -> Settings:
    """Get or create the singleton Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings(env_path)
    return _settings
