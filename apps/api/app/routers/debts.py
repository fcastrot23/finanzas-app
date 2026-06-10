"""Debts router — avalanche ordering and payoff projection."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import AvalancheResponse
from app.security.auth import get_current_uid, require_household_member

router = APIRouter(prefix="/households/{household_id}", tags=["debts"])


@router.get("/debts/avalanche", response_model=AvalancheResponse)
def get_avalanche(
    household_id: str,
    uid: str = Depends(get_current_uid),
) -> AvalancheResponse:
    """Return debts ordered by avalanche strategy (highest rate first). Core: API-1.6."""
    require_household_member(uid, household_id)
    from app.core.debts import avalanche_order
    from app.db.firestore import get_db

    return avalanche_order(get_db(), household_id)
