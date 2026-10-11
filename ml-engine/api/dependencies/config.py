"""
API Dependency Injection
========================

FastAPI dependency functions for configuration and shared state.
"""

from fx_risk_engine.config.settings import Settings, get_settings
from api.services.scenario_service import SessionStore, get_session_store


def get_app_settings() -> Settings:
    """Dependency: returns the application Settings singleton."""
    return get_settings()


def get_store() -> SessionStore:
    """Dependency: returns the global SessionStore singleton."""
    return get_session_store()
