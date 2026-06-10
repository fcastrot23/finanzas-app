"""Comparison router — plan vs actual deviation by month."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import ComparisonResponse
from app.security.auth import get_current_uid, require_household_member

router = APIRouter(prefix="/households/{household_id}", tags=["comparison"])


@router.get("/comparison/{month}", response_model=ComparisonResponse)
def get_comparison(
    household_id: str,
    month: str,
    uid: str = Depends(get_current_uid),
) -> ComparisonResponse:
    """Plan vs actual deviation for the given month (YYYY-MM). Core: API-1.5/1.6."""
    require_household_member(uid, household_id)
    from app.core.comparison import compare_plan_actual
    from app.db.firestore import get_db

    return compare_plan_actual(get_db(), household_id, month)
