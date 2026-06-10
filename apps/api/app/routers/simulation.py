"""Simulation router — expense feasibility check (traffic light + trade-off)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import SimulateRequest, SimulateResponse
from app.security.auth import get_current_uid, require_household_member

router = APIRouter(prefix="/households/{household_id}", tags=["simulation"])


@router.post("/simulate", response_model=SimulateResponse)
def simulate_expense(
    household_id: str,
    body: SimulateRequest,
    uid: str = Depends(get_current_uid),
) -> SimulateResponse:
    """Check if a proposed expense is feasible: green / amber / red + trade-off. Core: API-2.1."""
    require_household_member(uid, household_id)
    from app.core.simulation import simulate_expense as core_simulate
    from app.db.firestore import get_db

    return core_simulate(get_db(), household_id, body)
