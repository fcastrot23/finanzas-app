"""Unit tests for app.core.comparison — pure, no live Firestore (mocked)."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.comparison import compare_plan_actual

# ── Firestore mock builder ────────────────────────────────────────────────────

def _make_doc(doc_id: str, data: dict, exists: bool = True) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id
    doc.exists = exists
    doc.to_dict.return_value = data
    return doc


def _make_db(
    *,
    active_plan: dict | None,
    plan_lines: list[dict],
    transactions: list[dict],
    pockets: dict[str, dict],  # pocket_id -> {name, currency}
) -> MagicMock:
    """Build a minimal Firestore mock for comparison tests."""
    db = MagicMock()

    # plans collection: .where(h).where(active).stream()
    plan_docs = (
        [_make_doc("plan_1", active_plan)] if active_plan else []
    )
    plans_query = MagicMock()
    plans_query.where.return_value.stream.return_value = iter(plan_docs)
    plans_query.stream.return_value = iter(plan_docs)

    # plan lines subcollection: plans/plan_1/lines
    line_docs = [_make_doc(f"line_{i}", ln) for i, ln in enumerate(plan_lines)]
    plan_doc_ref = MagicMock()
    plan_doc_ref.collection.return_value.stream.return_value = iter(line_docs)

    # transactions collection: .where(h).stream()
    tx_docs = [_make_doc(f"tx_{i}", t) for i, t in enumerate(transactions)]
    txs_col = MagicMock()
    txs_col.where.return_value.stream.return_value = iter(tx_docs)

    # pockets collection: .document(id).get()
    pockets_col = MagicMock()
    def _get_pocket(pid: str) -> MagicMock:
        if pid in pockets:
            return _make_doc(pid, pockets[pid])
        return _make_doc(pid, {}, exists=False)
    pockets_col.document.side_effect = lambda pid: MagicMock(
        get=MagicMock(return_value=_get_pocket(pid))
    )

    # Route db.collection() calls
    def _col(name: str) -> MagicMock:
        if name == "plans":
            return plans_query
        if name == "transactions":
            return txs_col
        if name == "pockets":
            return pockets_col
        return MagicMock()

    db.collection.side_effect = _col

    # Route plans.document(id).collection("lines")
    def _plans_document(doc_id: str) -> MagicMock:
        return plan_doc_ref

    plans_query.document.side_effect = _plans_document

    return db


# ── Pilot household constants ─────────────────────────────────────────────────

HH_ID = "hh_fau_mari"
MONTH = "2026-06"

POCKETS = {
    "pocket_fau_usd": {"name": "Fau — dólares", "currency": "USD"},
    "pocket_mari_crc": {"name": "Mari — colones", "currency": "CRC"},
}

ACTIVE_PLAN = {
    "householdId": HH_ID,
    "status": "active",
    "period": {"from": "2026-06-01", "to": "2026-08-31"},
}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestComparePlanActual:

    def test_no_active_plan_returns_empty(self) -> None:
        db = _make_db(
            active_plan=None,
            plan_lines=[],
            transactions=[],
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        assert result.items == []
        assert result.total_planned == Decimal("0")
        assert result.total_actual == Decimal("0")

    def test_plan_only_no_transactions(self) -> None:
        """Plan has a line; no actual transactions → big negative delta."""
        lines = [
            {"pocketId": "pocket_fau_usd", "date": "2026-06-14", "amount": "2018.65", "currency": "USD"},
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=lines,
            transactions=[],
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.pocket_id == "pocket_fau_usd"
        assert item.planned == Decimal("2018.65")
        assert item.actual == Decimal("0")
        assert item.delta == Decimal("-2018.65")

    def test_transaction_only_no_plan(self) -> None:
        """Transaction exists but no plan lines → unplanned actual."""
        txs = [
            {"householdId": HH_ID, "pocketId": "pocket_fau_usd", "date": "2026-06-06",
             "amount": "800", "currency": "USD"},
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=[],
            transactions=txs,
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.planned == Decimal("0")
        assert item.actual == Decimal("800")
        assert item.delta == Decimal("800")

    def test_pilot_fau_on_budget(self) -> None:
        """Pilot: Fau planned $800 BAC; actually paid $800 → delta 0."""
        lines = [
            {"pocketId": "pocket_fau_usd", "date": "2026-06-06", "amount": "800", "currency": "USD"},
        ]
        txs = [
            {"householdId": HH_ID, "pocketId": "pocket_fau_usd", "date": "2026-06-06",
             "amount": "800", "currency": "USD"},
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=lines,
            transactions=txs,
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.delta == Decimal("0")
        assert item.delta_pct == Decimal("0.00")

    def test_pilot_overspend(self) -> None:
        """Pilot: Planned ₡120k escuela; Mari paid ₡120k + extra ₡17.9k Moose = ₡137.9k."""
        lines = [
            {"pocketId": "pocket_mari_crc", "date": "2026-06-06", "amount": "120000", "currency": "CRC"},
        ]
        txs = [
            {"householdId": HH_ID, "pocketId": "pocket_mari_crc", "date": "2026-06-06",
             "amount": "120000", "currency": "CRC"},
            {"householdId": HH_ID, "pocketId": "pocket_mari_crc", "date": "2026-06-07",
             "amount": "17900", "currency": "CRC"},
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=lines,
            transactions=txs,
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        item = result.items[0]
        assert item.planned == Decimal("120000")
        assert item.actual == Decimal("137900")
        assert item.delta == Decimal("17900")
        assert item.delta_pct is not None
        assert item.delta_pct == pytest.approx(Decimal("14.92"), abs=Decimal("0.01"))

    def test_filters_out_different_month_lines(self) -> None:
        """Lines and transactions from July must not appear in June comparison."""
        lines = [
            {"pocketId": "pocket_fau_usd", "date": "2026-06-14", "amount": "2018.65", "currency": "USD"},
            {"pocketId": "pocket_fau_usd", "date": "2026-07-14", "amount": "2018.65", "currency": "USD"},  # July
        ]
        txs = [
            {"householdId": HH_ID, "pocketId": "pocket_fau_usd", "date": "2026-07-05",
             "amount": "500", "currency": "USD"},  # July
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=lines,
            transactions=txs,
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        # Only June line ($2018.65) and no transactions for June
        assert len(result.items) == 1
        assert result.items[0].planned == Decimal("2018.65")
        assert result.items[0].actual == Decimal("0")

    def test_two_pockets_independent(self) -> None:
        """USD and CRC pockets produce separate items (currencies don't mix)."""
        lines = [
            {"pocketId": "pocket_fau_usd", "date": "2026-06-14", "amount": "2018.65", "currency": "USD"},
            {"pocketId": "pocket_mari_crc", "date": "2026-06-06", "amount": "120000", "currency": "CRC"},
        ]
        txs = [
            {"householdId": HH_ID, "pocketId": "pocket_fau_usd", "date": "2026-06-14",
             "amount": "2018.65", "currency": "USD"},
            {"householdId": HH_ID, "pocketId": "pocket_mari_crc", "date": "2026-06-06",
             "amount": "120000", "currency": "CRC"},
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=lines,
            transactions=txs,
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        assert len(result.items) == 2
        for item in result.items:
            assert item.delta == Decimal("0")

    def test_pocket_name_populated(self) -> None:
        lines = [
            {"pocketId": "pocket_fau_usd", "date": "2026-06-14", "amount": "100", "currency": "USD"},
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=lines,
            transactions=[],
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        assert result.items[0].pocket_name == "Fau — dólares"

    def test_totals_match_sum_of_items(self) -> None:
        lines = [
            {"pocketId": "pocket_fau_usd", "date": "2026-06-14", "amount": "2018.65", "currency": "USD"},
            {"pocketId": "pocket_mari_crc", "date": "2026-06-06", "amount": "120000", "currency": "CRC"},
        ]
        txs = [
            {"householdId": HH_ID, "pocketId": "pocket_fau_usd", "date": "2026-06-14",
             "amount": "1800", "currency": "USD"},
        ]
        db = _make_db(
            active_plan=ACTIVE_PLAN,
            plan_lines=lines,
            transactions=txs,
            pockets=POCKETS,
        )
        result = compare_plan_actual(db, HH_ID, MONTH)
        assert result.total_planned == sum(i.planned for i in result.items)
        assert result.total_actual == sum(i.actual for i in result.items)
        assert result.total_delta == result.total_actual - result.total_planned
