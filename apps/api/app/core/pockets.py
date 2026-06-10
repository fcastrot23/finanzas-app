"""pockets — balance tracking, currency integrity, and transfer support.

Rules (enforced here):
- Each pocket has exactly one currency (CRC or USD); it never changes.
- A transaction's currency MUST match the pocket's currency. No implicit conversion.
- Transfers between pockets are recorded as matching debit/credit pairs in each pocket.
- The LLM never touches pocket balances directly — it calls these functions.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.core.money import Money


@dataclass
class PocketSnapshot:
    """Read-only view of a pocket and its current balance."""

    pocket_id: str
    name: str
    owner_uid: str | None
    currency: str
    balance: Money


def pocket_balance(db: Any, pocket_id: str) -> Money:
    """Compute the current balance of a pocket by summing its transactions.

    Returns a Money in the pocket's currency.
    Raises ValueError if a transaction currency doesn't match the pocket.
    """
    pocket_doc = db.collection("pockets").document(pocket_id).get()
    if not pocket_doc.exists:
        raise ValueError(f"Pocket '{pocket_id}' not found")
    pocket = pocket_doc.to_dict()
    pocket_currency: str = pocket["currency"]

    txs = db.collection("transactions").where("pocketId", "==", pocket_id).stream()
    balance = Money(Decimal("0"), pocket_currency)

    for tx in txs:
        d = tx.to_dict()
        amount_raw = Decimal(str(d["amount"]))
        tx_currency: str = d["currency"]

        assert_no_currency_cross(pocket_currency, tx_currency, context=f"transaction {tx.id}")

        tx_type: str = d.get("type", "expense")
        tx_money = Money(amount_raw, pocket_currency)

        if tx_type in ("income", "opening_balance"):
            balance = balance + tx_money
        else:
            # expense, debt_payment, transfer, leisure → subtract
            balance = balance - tx_money

    return balance


def pocket_snapshot(db: Any, pocket_id: str) -> PocketSnapshot:
    """Return a PocketSnapshot with metadata and current balance."""
    pocket_doc = db.collection("pockets").document(pocket_id).get()
    if not pocket_doc.exists:
        raise ValueError(f"Pocket '{pocket_id}' not found")
    p = pocket_doc.to_dict()
    bal = pocket_balance(db, pocket_id)
    return PocketSnapshot(
        pocket_id=pocket_id,
        name=p["name"],
        owner_uid=p.get("ownerUid"),
        currency=p["currency"],
        balance=bal,
    )


def household_pockets(db: Any, household_id: str) -> list[PocketSnapshot]:
    """Return snapshots for all pockets in the household."""
    docs = db.collection("pockets").where("householdId", "==", household_id).stream()
    return [pocket_snapshot(db, doc.id) for doc in docs]


def assert_no_currency_cross(
    pocket_currency: str,
    tx_currency: str,
    context: str = "",
) -> None:
    """Raise ValueError if currencies don't match.

    Called before every transaction write. The LLM never bypasses this.
    """
    if pocket_currency != tx_currency:
        extra = f" ({context})" if context else ""
        raise ValueError(
            f"Currency mismatch{extra}: pocket is {pocket_currency}, "
            f"transaction is {tx_currency}. "
            "Pockets never mix currencies — register in the correct pocket or "
            "convert explicitly with an FX rate."
        )


def validate_transfer(
    source_pocket: dict,
    dest_pocket: dict,
    amount: Decimal,
    fx_rate: Decimal | None = None,
) -> tuple[bool, str]:
    """Validate a transfer between two pockets.

    Returns (is_valid, error_message).
    If both pockets are the same currency: direct transfer, no FX needed.
    If currencies differ: fx_rate required.
    """
    src_currency = source_pocket["currency"]
    dst_currency = dest_pocket["currency"]

    if amount <= 0:
        return False, "Transfer amount must be positive"

    if src_currency == dst_currency:
        return True, ""

    if fx_rate is None:
        return (
            False,
            f"FX rate required to transfer from {src_currency} pocket to {dst_currency} pocket",
        )

    if fx_rate <= 0:
        return False, "FX rate must be positive"

    return True, ""
