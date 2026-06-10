"""Leisure router — individual and household budget status."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import LeisureStatus
from app.security.auth import get_current_uid, require_household_member

router = APIRouter(prefix="/households/{household_id}", tags=["leisure"])


@router.get("/leisure/status", response_model=LeisureStatus)
def get_leisure_status(
    household_id: str,
    uid: str = Depends(get_current_uid),
) -> LeisureStatus:
    """Current leisure budget consumption: available, spent, caps. Core: API-2.2."""
    require_household_member(uid, household_id)
    from app.core.leisure import leisure_status
    from app.db.firestore import get_db

    return leisure_status(get_db(), household_id)
