"""simulation — expense feasibility check. Full implementation in API-2.1."""
from __future__ import annotations

from typing import Any


def simulate_expense(db: Any, household_id: str, body: Any) -> Any:
    """Check if a proposed expense is feasible and return traffic light + trade-off.

    Full logic lands in API-2.1 (Phase 2).
    """
    from app.models.schemas import SimulateResponse, TrafficLight

    # Stub: always green until real simulation is implemented
    return SimulateResponse(
        light=TrafficLight.green,
        feasible=True,
        sacrifice=None,
        source=None,
        detail="Simulación pendiente de implementación completa (Fase 2).",
    )
