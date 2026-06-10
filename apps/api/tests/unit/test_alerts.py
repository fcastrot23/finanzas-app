"""Unit tests for app.core.alerts — generate_alerts and close_month."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.core.alerts import generate_alerts, close_month

HH_ID = "hh_fau_mari"
MONTH = "2026-06"
POCKET_USD = "pocket_fau_usd"
POCKET_CRC = "pocket_mari_crc"


# ── Firestore mock helpers ────────────────────────────────────────────────────

def _make_doc(doc_id: str, data: dict, exists: bool = True) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id
    doc.exists = exists
    doc.to_dict.return_value = data
    doc.reference = MagicMock()
    return doc


def _make_db(
    *,
    plan_lines: list[dict],
    txs: list[dict],
    pockets: dict[str, dict] | None = None,
    has_active_plan: bool = True,
) -> MagicMock:
    """Build a Firestore mock suitable for generate_alerts and close_month.

    Uses side_effect=lambda: iter(...) on all .stream() calls so that
    multiple consumers (compare_plan_actual + _count_unmatched + generate_alerts)
    each get a fresh iterator.
    """
    pockets = pockets or {
        POCKET_USD: {"name": "Fau USD", "currency": "USD"},
        POCKET_CRC: {"name": "Mari CRC", "currency": "CRC"},
    }

    plan_data = {"householdId": HH_ID, "status": "active",
                 "period": {"from": "2026-06-01", "to": "2026-08-31"}}
    plan_doc = _make_doc("plan_1", plan_data)
    line_docs = [_make_doc(f"ln_{i}", ln) for i, ln in enumerate(plan_lines)]
    tx_docs = [_make_doc(f"tx_{i}", t) for i, t in enumerate(txs)]

    # plans subcollection (lines)
    plan_ref = MagicMock()
    plan_ref.collection.return_value.stream.side_effect = lambda: iter(line_docs)

    # plans where chain — fresh plan_doc stream each time
    second_where = MagicMock()
    second_where.stream.side_effect = lambda: iter([plan_doc] if has_active_plan else [])
    first_where = MagicMock()
    first_where.where.return_value = second_where

    plans_col = MagicMock()
    plans_col.where.return_value = first_where
    plans_col.document.return_value = plan_ref

    # transactions — fresh each time
    txs_col = MagicMock()
    txs_col.where.return_value.stream.side_effect = lambda: iter(tx_docs)

    # pockets
    pockets_col = MagicMock()
    def _get_pocket(pid: str) -> MagicMock:
        if pid in pockets:
            return _make_doc(pid, pockets[pid])
        return _make_doc(pid, {}, exists=False)
    pockets_col.document.side_effect = lambda pid: MagicMock(
        get=MagicMock(return_value=_get_pocket(pid))
    )

    db = MagicMock()
    db.collection.side_effect = lambda name: {
        "plans": plans_col,
        "transactions": txs_col,
        "pockets": pockets_col,
    }.get(name, MagicMock())
    return db


# ── generate_alerts ───────────────────────────────────────────────────────────

class TestGenerateAlerts:
    def test_no_alerts_when_on_budget(self) -> None:
        """Planned == actual → no overspend or near_cap alerts."""
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-15", "amount": "800", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-15",
                 "amount": "800", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = generate_alerts(db, HH_ID, MONTH)
        assert all(a.type not in ("overspend", "near_cap") for a in result)

    def test_overspend_alert_when_actual_exceeds_planned(self) -> None:
        """Pilot: planned $800, actual $850 → red overspend alert."""
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-06", "amount": "800", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-06",
                 "amount": "850", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = generate_alerts(db, HH_ID, MONTH)
        overspend = [a for a in result if a.type == "overspend"]
        assert len(overspend) == 1
        alert = overspend[0]
        assert alert.severity.value == "red"
        assert alert.pocket_id == POCKET_USD
        assert "850" in alert.message

    def test_near_cap_alert_at_90_pct(self) -> None:
        """Actual = 90% of planned → amber near_cap alert."""
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-15", "amount": "1000", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-15",
                 "amount": "900", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = generate_alerts(db, HH_ID, MONTH)
        near_cap = [a for a in result if a.type == "near_cap"]
        assert len(near_cap) == 1
        assert near_cap[0].severity.value == "amber"

    def test_no_near_cap_below_80_pct(self) -> None:
        """70% usage → no near_cap alert."""
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-15", "amount": "1000", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-15",
                 "amount": "700", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = generate_alerts(db, HH_ID, MONTH)
        assert all(a.type != "near_cap" for a in result)

    def test_unmatched_tx_alert_for_out_of_plan(self) -> None:
        """Pilot: Moose (out_of_plan) → info alert about unmatched transactions."""
        db = _make_db(
            plan_lines=[],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_CRC, "date": f"{MONTH}-07",
                 "amount": "17900", "currency": "CRC", "status": "out_of_plan",
                 "concept": "Moose — salida familiar"},
            ],
        )
        result = generate_alerts(db, HH_ID, MONTH)
        unmatched = [a for a in result if a.type == "unmatched_tx"]
        assert len(unmatched) == 1
        assert unmatched[0].severity.value == "info"
        assert "1" in unmatched[0].message

    def test_no_unmatched_when_all_in_plan(self) -> None:
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-06", "amount": "800", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-06",
                 "amount": "800", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = generate_alerts(db, HH_ID, MONTH)
        assert all(a.type != "unmatched_tx" for a in result)

    def test_uses_today_month_when_no_month_given(self) -> None:
        """Without a month parameter, uses current month."""
        db = _make_db(plan_lines=[], txs=[])
        with patch("app.core.alerts.date") as mock_date:
            from datetime import date
            mock_date.today.return_value = date(2026, 6, 9)
            mock_date.strftime = date.strftime
            result = generate_alerts(db, HH_ID)
        assert isinstance(result, list)


# ── close_month ───────────────────────────────────────────────────────────────

class TestCloseMonth:
    def test_archives_active_plan_and_returns_id(self) -> None:
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-15", "amount": "800", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-15",
                 "amount": "800", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = close_month(db, HH_ID, MONTH)
        assert result.archived_plan_id == "plan_1"
        assert result.month == MONTH
        assert result.household_id == HH_ID

    def test_response_includes_totals(self) -> None:
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-15", "amount": "1000", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-15",
                 "amount": "1050", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = close_month(db, HH_ID, MONTH)
        assert result.total_planned == Decimal("1000")
        assert result.total_actual == Decimal("1050")
        assert result.total_delta == Decimal("50")

    def test_response_includes_overspend_alert(self) -> None:
        """Overspend in the closing month → alert appears in response."""
        db = _make_db(
            plan_lines=[
                {"pocketId": POCKET_USD, "date": f"{MONTH}-15", "amount": "800", "currency": "USD"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_USD, "date": f"{MONTH}-15",
                 "amount": "900", "currency": "USD", "status": "in_plan"},
            ],
        )
        result = close_month(db, HH_ID, MONTH)
        assert result.alert_count == len(result.alerts)
        overspend_alerts = [a for a in result.alerts if a.type == "overspend"]
        assert len(overspend_alerts) == 1

    def test_no_active_plan_returns_none_archived_id(self) -> None:
        db = _make_db(plan_lines=[], txs=[], has_active_plan=False)
        result = close_month(db, HH_ID, MONTH)
        assert result.archived_plan_id is None
        assert result.total_planned == Decimal("0")
