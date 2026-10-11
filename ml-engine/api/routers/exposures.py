"""
Exposures Router
================

Endpoints for uploading and managing company FX exposure profiles.
"""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.request_models import (
    UploadExposuresRequest,
    ExposureResponse,
)
from api.dependencies.config import get_store
from api.services.scenario_service import SessionStore
from fx_risk_engine.models.exposure import Exposure
from fx_risk_engine.models.profile import CompanyFXProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exposures", tags=["Exposures"])


@router.post(
    "",
    response_model=ExposureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload company FX exposures",
    description="Upload a company's FX exposure profile. Returns a profile ID for subsequent analysis.",
)
def upload_exposures(
    request: UploadExposuresRequest,
    store: SessionStore = Depends(get_store),
) -> ExposureResponse:
    """Upload company FX exposures and store them in-memory."""
    try:
        # Convert Pydantic models to domain objects
        exposures = [
            Exposure(
                name=e.name,
                exp_type=e.exp_type,
                amount=e.amount,
                currency=e.currency,
            )
            for e in request.exposures
        ]

        profile = CompanyFXProfile(
            company_name=request.company_name,
            base_currency=request.base_currency,
            exposures=exposures,
        )

        profile_id = store.store_profile(profile)

        logger.info(
            "Uploaded %d exposures for '%s' (profile_id=%s)",
            len(exposures),
            request.company_name,
            profile_id,
        )

        return ExposureResponse(
            status="created",
            company_name=request.company_name,
            base_currency=request.base_currency,
            num_exposures=len(exposures),
            profile_id=profile_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List stored profiles",
    description="List all uploaded company profiles with summary information.",
)
def list_profiles(
    store: SessionStore = Depends(get_store),
) -> List[Dict[str, Any]]:
    """List all stored company profiles."""
    return store.list_profiles()


@router.get(
    "/{profile_id}",
    summary="Get profile details",
    description="Retrieve a specific company profile by its ID.",
)
def get_profile(
    profile_id: str,
    store: SessionStore = Depends(get_store),
) -> Dict[str, Any]:
    """Get detailed information about a stored profile."""
    profile = store.get_profile(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found.",
        )
    return profile.to_dict()


@router.delete(
    "/{profile_id}",
    summary="Delete a profile",
    description="Remove a stored company profile.",
)
def delete_profile(
    profile_id: str,
    store: SessionStore = Depends(get_store),
) -> Dict[str, str]:
    """Delete a stored profile."""
    if store.delete_profile(profile_id):
        return {"status": "deleted", "profile_id": profile_id}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Profile '{profile_id}' not found.",
    )
