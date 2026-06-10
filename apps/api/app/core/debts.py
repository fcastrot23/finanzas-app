"""debts — avalanche ordering and payoff projection. Full implementation in API-1.6."""
from __future__ import annotations

from decimal import Decimal
from typing import Any


def avalanche_order(db: Any, household_id: str) -> Any:
    """Return household debts ordered by avalanche strategy (highest rate first).

    Full logic with payoff projection lands in API-1.6.
    """
    from app.models.schemas import AvalancheEntry, AvalancheResponse

    docs = db.collection("debts").where("householdId", "==", household_id).stream()
    entries: list[AvalancheEntry] = []
    for doc in docs:
        d = doc.to_dict()
        entries.append(
            AvalancheEntry(
                debt_id=doc.id,
                creditor=d["creditor"],
                balance=Decimal(str(d["balance"])),
                currency=d["currency"],
                rate=Decimal(str(d["rate"])),
                payment=Decimal(str(d["payment"])),
                priority=d.get("priority", 99),
            )
        )
    entries.sort(key=lambda e: e.rate, reverse=True)

    # Re-assign priority based on sorted order
    for i, e in enumerate(entries, start=1):
        e.priority = i

    # Convert all balances to USD (using stored currency; no FX conversion yet)
    total_usd = sum(
        e.balance for e in entries if e.currency == "USD"
    )

    return AvalancheResponse(
        household_id=household_id,
        debts=entries,
        total_balance_usd=total_usd,
    )
