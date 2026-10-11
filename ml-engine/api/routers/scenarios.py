"""
Scenarios Router
================

Endpoints for managing FX shock scenarios.
"""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.request_models import ScenarioInput, ScenarioResponse
from api.dependencies.config import get_store
from api.services.scenario_service import SessionStore
from fx_risk_engine.models.scenario import FXScenario

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List all scenarios",
    description="List all predefined and custom FX shock scenarios.",
)
def list_scenarios(
    store: SessionStore = Depends(get_store),
) -> List[Dict[str, Any]]:
    """List all available scenarios."""
    return store.list_scenarios()


@router.post(
    "",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scenario",
    description="Define a custom FX shock scenario.",
)
def create_scenario(
    request: ScenarioInput,
    store: SessionStore = Depends(get_store),
) -> ScenarioResponse:
    """Create and register a new FX scenario."""
    try:
        scenario = FXScenario(
            name=request.name,
            shock_percentages=request.shock_percentages,
            description=request.description,
            created_by="api_user",
        )
        store.add_scenario(scenario)

        logger.info("Created scenario: %s", scenario.name)

        return ScenarioResponse(
            name=scenario.name,
            shock_percentages=scenario.shock_percentages,
            description=scenario.description,
            created_at=scenario.created_at,
            created_by=scenario.created_by,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )


@router.get(
    "/{scenario_name}",
    response_model=ScenarioResponse,
    summary="Get scenario details",
    description="Retrieve a specific scenario by name.",
)
def get_scenario(
    scenario_name: str,
    store: SessionStore = Depends(get_store),
) -> ScenarioResponse:
    """Get a specific scenario."""
    scenario = store.get_scenario(scenario_name)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_name}' not found.",
        )
    return ScenarioResponse(
        name=scenario.name,
        shock_percentages=scenario.shock_percentages,
        description=scenario.description,
        created_at=scenario.created_at,
        created_by=scenario.created_by,
    )


@router.delete(
    "/{scenario_name}",
    summary="Delete a scenario",
    description="Remove a custom scenario by name.",
)
def delete_scenario(
    scenario_name: str,
    store: SessionStore = Depends(get_store),
) -> Dict[str, str]:
    """Delete a scenario."""
    if store.remove_scenario(scenario_name):
        return {"status": "deleted", "scenario_name": scenario_name}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Scenario '{scenario_name}' not found.",
    )
