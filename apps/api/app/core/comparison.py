"""comparison — plan vs actual deviation by pocket for a given month.

Logic:
- Fetches the household's active plan and its lines for the requested month.
- Fetches transactions for the same household + month.
- Groups both by pocket_id and computes planned / actual / delta.
- Returns a ComparisonResponse with one DeviationItem per pocket.

Note on cross-currency totals:
  total_planned / total_actual / total_delta in ComparisonResponse are raw
  decimal sums across all pockets. They are only meaningful when all pockets
  share the same currency. Multi-currency aggregation belongs in the simulate
  endpoint (with an explicit FX rate). The per-pocket DeviationItem list is
  the authoritative output here.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any


def compare_plan_actual(db: Any, household_id: str, month: str) -> Any:
    """Compare planned vs actual amounts for every pocket in a given month.

    Args:
        db: Firestore client (Firebase Admin SDK).
        household_id: e.g. "hh_fau_mari".
        month: "YYYY-MM" (e.g. "2026-06").

    Returns:
        ComparisonResponse with items=[DeviationItem, ...].
    """
    from app.models.schemas import ComparisonResponse, Currency, DeviationItem

    # ── 1. Find the active plan for this household ────────────────────────────
    plans_stream = (
        db.collection("plans")
        .where("householdId", "==", household_id)
        .where("status", "==", "active")
        .stream()
    )
    active_plan_doc = next(plans_stream, None)

    # ── 2. Collect plan lines for the requested month ─────────────────────────
    planned_by_pocket: dict[str, Decimal] = {}
    pocket_currency: dict[str, str] = {}  # pocket_id -> currency

    if active_plan_doc is not None:
        plan_id: str = active_plan_doc.id
        lines_stream = (
            db.collection("plans")
            .document(plan_id)
            .collection("lines")
            .stream()
        )
        for line_doc in lines_stream:
            line = line_doc.to_dict()
            line_date: str = str(line.get("date", ""))
            if line_date[:7] != month:
                continue
            pocket_id: str = line.get("pocketId", "")
            amount = Decimal(str(line.get("amount", "0")))
            currency: str = line.get("currency", "CRC")

            planned_by_pocket[pocket_id] = planned_by_pocket.get(pocket_id, Decimal("0")) + amount
            pocket_currency.setdefault(pocket_id, currency)

    # ── 3. Collect actual transactions for the requested month ────────────────
    actual_by_pocket: dict[str, Decimal] = {}

    txs_stream = (
        db.collection("transactions")
        .where("householdId", "==", household_id)
        .stream()
    )
    for tx_doc in txs_stream:
        tx = tx_doc.to_dict()
        tx_date: str = str(tx.get("date", ""))
        if tx_date[:7] != month:
            continue
        pocket_id = tx.get("pocketId", "")
        amount = Decimal(str(tx.get("amount", "0")))
        tx_currency: str = tx.get("currency", "CRC")

        actual_by_pocket[pocket_id] = actual_by_pocket.get(pocket_id, Decimal("0")) + amount
        pocket_currency.setdefault(pocket_id, tx_currency)

    # ── 4. Fetch pocket names (one read per pocket) ───────────────────────────
    all_pocket_ids = sorted(
        set(planned_by_pocket.keys()) | set(actual_by_pocket.keys())
    )
    pocket_name: dict[str, str] = {}
    for pid in all_pocket_ids:
        doc = db.collection("pockets").document(pid).get()
        if doc.exists:
            pocket_name[pid] = doc.to_dict().get("name", pid)
            pocket_currency.setdefault(pid, doc.to_dict().get("currency", "CRC"))
        else:
            pocket_name[pid] = pid

    # ── 5. Build DeviationItem list ───────────────────────────────────────────
    items: list[DeviationItem] = []
    for pid in all_pocket_ids:
        planned = planned_by_pocket.get(pid, Decimal("0"))
        actual = actual_by_pocket.get(pid, Decimal("0"))
        delta = actual - planned
        delta_pct: Decimal | None = (
            (delta / planned * Decimal("100")).quantize(Decimal("0.01"))
            if planned != Decimal("0")
            else None
        )
        currency_str = pocket_currency.get(pid, "CRC")
        items.append(
            DeviationItem(
                pocket_id=pid,
                pocket_name=pocket_name.get(pid, pid),
                currency=Currency(currency_str),
                planned=planned,
                actual=actual,
                delta=delta,
                delta_pct=delta_pct,
            )
        )

    # ── 6. Totals (per-currency sum; see module docstring on cross-currency) ──
    total_planned = sum((i.planned for i in items), Decimal("0"))
    total_actual = sum((i.actual for i in items), Decimal("0"))

    return ComparisonResponse(
        month=month,
        household_id=household_id,
        items=items,
        total_planned=total_planned,
        total_actual=total_actual,
        total_delta=total_actual - total_planned,
    )
