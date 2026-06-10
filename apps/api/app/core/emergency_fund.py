"""emergency_fund — target and progress. Full implementation in API-2.3."""
from __future__ import annotations

from decimal import Decimal


def emergency_fund_progress(saved: Decimal, target: Decimal) -> dict:
    """Return progress towards the emergency fund target."""
    if target <= 0:
        return {"saved": saved, "target": target, "pct": Decimal("100"), "remaining": Decimal("0")}
    pct = (saved / target * 100).quantize(Decimal("0.1"))
    remaining = max(Decimal("0"), target - saved)
    return {"saved": saved, "target": target, "pct": pct, "remaining": remaining}
