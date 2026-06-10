"""Close-month router — triggered by Cloud Scheduler or manually."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.security.auth import get_current_uid, require_household_member

router = APIRouter(prefix="/households/{household_id}", tags=["close-month"])


@router.post("/close-month")
def close_month(
    household_id: str,
    uid: str = Depends(get_current_uid),
) -> dict[str, str]:
    """Archive the current month, generate summary, seed next month plan. API-2.12/2.13."""
    require_household_member(uid, household_id)
    # TODO: implement in Phase 2
    return {"status": "not_implemented", "message": "Cierre de mes disponible en Fase 2"}
