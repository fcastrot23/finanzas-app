"""leisure — budget status and available balance. Full implementation in API-2.2."""
from __future__ import annotations

from datetime import date
from typing import Any


def leisure_status(db: Any, household_id: str) -> Any:
    """Return leisure budget consumption for the current month.

    Full logic with 50/50 household split lands in API-2.2.
    """
    from app.models.schemas import LeisureStatus

    today = date.today()
    period_start = today.replace(day=1)
    period_end = today.replace(day=28)  # safe last day placeholder

    return LeisureStatus(
        household_id=household_id,
        period_start=period_start,
        period_end=period_end,
        individual=[],
        household_budget=None,
    )
