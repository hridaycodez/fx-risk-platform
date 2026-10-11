"""
Scenario Service
=================

In-memory session storage for uploaded profiles and scenarios.
Acts as a business logic layer between API routes and the analytics engine.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any

from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.models.profile import CompanyFXProfile
from fx_risk_engine.models.scenario import FXScenario
from fx_risk_engine.analytics.stress import ScenarioManager, PREDEFINED_SCENARIOS

logger = logging.getLogger(__name__)


class SessionStore:
    """
    In-memory store for company profiles and scenarios.

    In production, this would be backed by a database.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, CompanyFXProfile] = {}
        self._scenario_manager = ScenarioManager()

    # ── Profile Management ────────────────────────────────────────

    def store_profile(self, profile: CompanyFXProfile) -> str:
        """
        Store a company profile and return a unique ID.

        Args:
            profile: CompanyFXProfile to store.

        Returns:
            Generated profile ID.
        """
        profile_id = str(uuid.uuid4())[:8]
        self._profiles[profile_id] = profile
        logger.info(
            "Stored profile '%s' for %s with %d exposures",
            profile_id,
            profile.company_name,
            len(profile.exposures),
        )
        return profile_id

    def get_profile(self, profile_id: str) -> Optional[CompanyFXProfile]:
        """Retrieve a profile by ID."""
        return self._profiles.get(profile_id)

    def list_profiles(self) -> List[Dict[str, Any]]:
        """List all stored profiles with summary info."""
        return [
            {
                "profile_id": pid,
                "company_name": p.company_name,
                "base_currency": p.base_currency,
                "num_exposures": len(p.exposures),
                "created_at": p.created_at,
            }
            for pid, p in self._profiles.items()
        ]

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile by ID."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            return True
        return False

    # ── Scenario Management ───────────────────────────────────────

    def add_scenario(self, scenario: FXScenario) -> None:
        """Add a scenario to the manager."""
        self._scenario_manager.add_scenario(scenario)

    def get_scenario(self, name: str) -> Optional[FXScenario]:
        """Get a scenario by name."""
        return self._scenario_manager.get_scenario(name)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all available scenarios."""
        return self._scenario_manager.list_scenarios()

    def remove_scenario(self, name: str) -> bool:
        """Remove a scenario by name."""
        return self._scenario_manager.remove_scenario(name)

    # ── Helper ────────────────────────────────────────────────────

    def get_exposures(
        self,
        profile_id: Optional[str] = None,
        inline_exposures: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Exposure]:
        """
        Resolve exposures from either a stored profile or inline data.

        Args:
            profile_id: ID of a stored profile.
            inline_exposures: List of exposure dicts provided inline.

        Returns:
            List of Exposure objects.

        Raises:
            ValueError: If neither source provides exposures.
        """
        if profile_id:
            profile = self.get_profile(profile_id)
            if profile:
                return profile.exposures
            raise ValueError(f"Profile '{profile_id}' not found.")

        if inline_exposures:
            return [
                Exposure(
                    name=e["name"],
                    exp_type=e["exp_type"],
                    amount=e["amount"],
                    currency=e["currency"],
                )
                for e in inline_exposures
            ]

        raise ValueError(
            "Either profile_id or inline exposures must be provided."
        )


# Global session store instance
_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get or create the global SessionStore."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
