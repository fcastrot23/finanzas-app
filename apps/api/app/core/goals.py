"""goals — sinking funds and progress projection. Full implementation in API-2.3."""
from __future__ import annotations

from datetime import date
from decimal import Decimal


def goal_progress(saved: Decimal, target: Decimal, target_date: date | None = None) -> dict:
    """Return progress and monthly contribution needed to reach goal by target_date."""
    remaining = max(Decimal("0"), target - saved)
    pct = (saved / target * 100).quantize(Decimal("0.1")) if target > 0 else Decimal("100")
    monthly_needed: Decimal | None = None
    if target_date and remaining > 0:
        today = date.today()
        months = max(1, (target_date.year - today.year) * 12 + (target_date.month - today.month))
        monthly_needed = (remaining / months).quantize(Decimal("0.01"))
    return {
        "saved": saved,
        "target": target,
        "remaining": remaining,
        "pct": pct,
        "monthly_needed": monthly_needed,
    }
