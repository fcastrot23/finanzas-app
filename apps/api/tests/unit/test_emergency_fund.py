"""Unit tests for app.core.emergency_fund — pure math + Firestore-backed."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.emergency_fund import emergency_fund_progress, emergency_fund_status

HH_ID = "hh_fau_mari"
FUND_POCKET = "pocket_emergency_crc"


def _make_doc(doc_id: str, data: dict, exists: bool = True) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id
    doc.exists = exists
    doc.to_dict.return_value = data
    return doc


def _make_db(*, fund_docs: list[dict], pocket_balance_amount: str = "0") -> MagicMock:
    """Build a Firestore mock for emergency_fund_status."""
    ef_docs = [_make_doc(f"ef_{i}", d) for i, d in enumerate(fund_docs)]
    ef_col = MagicMock()
    ef_col.where.return_value.stream.return_value = iter(ef_docs)

    # pocket_balance reads: pockets.document(id).get() + transactions.where(pocketId).stream()
    pocket_doc = _make_doc(FUND_POCKET, {"currency": "CRC", "name": "Fondo emergencia"})
    pockets_col = MagicMock()
    pockets_col.document.return_value.get.return_value = pocket_doc

    balance_tx = _make_doc("btx_0", {
        "pocketId": FUND_POCKET, "amount": pocket_balance_amount,
        "currency": "CRC", "type": "opening_balance",
    })
    txs_col = MagicMock()
    txs_col.where.return_value.stream.return_value = iter([balance_tx])

    db = MagicMock()
    db.collection.side_effect = lambda name: {
        "emergencyFunds": ef_col,
        "pockets": pockets_col,
        "transactions": txs_col,
    }.get(name, MagicMock())
    return db


# ── Pure math ─────────────────────────────────────────────────────────────────

class TestEmergencyFundProgress:
    def test_zero_saved(self) -> None:
        result = emergency_fund_progress(Decimal("0"), Decimal("500000"))
        assert result["pct"] == Decimal("0.0")
        assert result["remaining"] == Decimal("500000")

    def test_fully_funded(self) -> None:
        result = emergency_fund_progress(Decimal("500000"), Decimal("500000"))
        assert result["pct"] == Decimal("100.0")
        assert result["remaining"] == Decimal("0")

    def test_partial_progress(self) -> None:
        result = emergency_fund_progress(Decimal("250000"), Decimal("500000"))
        assert result["pct"] == Decimal("50.0")
        assert result["remaining"] == Decimal("250000")

    def test_over_funded_remaining_is_zero(self) -> None:
        result = emergency_fund_progress(Decimal("600000"), Decimal("500000"))
        assert result["remaining"] == Decimal("0")
        assert result["pct"] == Decimal("120.0")

    def test_zero_target_returns_100_pct(self) -> None:
        result = emergency_fund_progress(Decimal("0"), Decimal("0"))
        assert result["pct"] == Decimal("100")

    def test_pilot_crc_fund(self) -> None:
        """Pilot: target ₡1,311,667 (3-month emergency fund), saved ₡500,000 → ~38.1%."""
        result = emergency_fund_progress(Decimal("500000"), Decimal("1311667"))
        assert result["pct"] == pytest.approx(Decimal("38.1"), abs=Decimal("0.1"))
        assert result["remaining"] == Decimal("811667")


# ── Firestore-backed ──────────────────────────────────────────────────────────

class TestEmergencyFundStatus:
    def test_no_funds_returns_empty_list(self) -> None:
        db = _make_db(fund_docs=[])
        result = emergency_fund_status(db, HH_ID)
        assert result == []

    def test_single_fund_reads_pocket_balance(self) -> None:
        """pocket_balance is used to determine 'saved', not the stored field."""
        db = _make_db(
            fund_docs=[{
                "householdId": HH_ID,
                "target": "1311667",
                "pocketId": FUND_POCKET,
                "currency": "CRC",
                "monthsTarget": 3,
            }],
            pocket_balance_amount="500000",
        )
        result = emergency_fund_status(db, HH_ID)
        assert len(result) == 1
        status = result[0]
        assert status.household_id == HH_ID
        assert status.target == Decimal("1311667")
        assert status.saved == Decimal("500000")
        assert status.remaining == Decimal("811667")
        assert status.pct == pytest.approx(Decimal("38.1"), abs=Decimal("0.1"))
        assert status.months_target == 3
        assert status.currency.value == "CRC"

    def test_fully_funded_shows_zero_remaining(self) -> None:
        db = _make_db(
            fund_docs=[{
                "householdId": HH_ID,
                "target": "500000",
                "pocketId": FUND_POCKET,
                "currency": "CRC",
            }],
            pocket_balance_amount="500000",
        )
        result = emergency_fund_status(db, HH_ID)
        assert result[0].remaining == Decimal("0")
        assert result[0].pct == Decimal("100.0")

    def test_months_target_none_when_not_set(self) -> None:
        db = _make_db(
            fund_docs=[{
                "householdId": HH_ID,
                "target": "500000",
                "pocketId": FUND_POCKET,
                "currency": "CRC",
            }],
            pocket_balance_amount="0",
        )
        result = emergency_fund_status(db, HH_ID)
        assert result[0].months_target is None
