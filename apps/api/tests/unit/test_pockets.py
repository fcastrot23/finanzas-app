"""Unit tests for app.core.pockets — pure, no I/O (Firestore is mocked)."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.money import Money
from app.core.pockets import (
    assert_no_currency_cross,
    pocket_balance,
    validate_transfer,
)

# ── DB stubs ──────────────────────────────────────────────────────────────────

def _pocket_doc(pocket_id: str, currency: str, name: str = "Test Pocket", owner: str | None = None) -> MagicMock:
    doc = MagicMock()
    doc.exists = True
    doc.id = pocket_id
    doc.to_dict.return_value = {
        "householdId": "hh_fau_mari",
        "currency": currency,
        "name": name,
        "ownerUid": owner,
    }
    return doc


def _tx_doc(tx_id: str, amount: str, currency: str, tx_type: str) -> MagicMock:
    doc = MagicMock()
    doc.id = tx_id
    doc.to_dict.return_value = {
        "amount": amount,
        "currency": currency,
        "type": tx_type,
        "pocketId": "pocket_fau_usd",
    }
    return doc


def _make_db(pocket: MagicMock, transactions: list[MagicMock]) -> MagicMock:
    db = MagicMock()

    # pockets collection
    pockets_col = MagicMock()
    pockets_col.document.return_value.get.return_value = pocket

    # transactions collection (with where().stream())
    txs_col = MagicMock()
    txs_col.where.return_value.stream.return_value = iter(transactions)

    def collection_selector(name: str) -> MagicMock:
        if name == "pockets":
            return pockets_col
        return txs_col

    db.collection.side_effect = collection_selector
    return db


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPocketBalance:
    def test_empty_pocket_is_zero(self) -> None:
        pocket = _pocket_doc("p1", "USD")
        db = _make_db(pocket, [])
        result = pocket_balance(db, "p1")
        assert result == Money("0", "USD")

    def test_income_adds_to_balance(self) -> None:
        pocket = _pocket_doc("pocket_fau_usd", "USD")
        txs = [
            _tx_doc("t1", "2018.65", "USD", "income"),
            _tx_doc("t2", "4295.00", "USD", "income"),
        ]
        db = _make_db(pocket, txs)
        result = pocket_balance(db, "pocket_fau_usd")
        assert result.amount == Decimal("6313.65")
        assert result.currency == "USD"

    def test_expense_subtracts_from_balance(self) -> None:
        pocket = _pocket_doc("pocket_mari_crc", "CRC")
        txs = [
            _tx_doc("t1", "1311667", "CRC", "income"),
            _tx_doc("t2", "200000", "CRC", "expense"),
            _tx_doc("t3", "150000", "CRC", "expense"),
        ]
        db = _make_db(pocket, txs)
        result = pocket_balance(db, "pocket_mari_crc")
        assert result.amount == Decimal("961667")
        assert result.currency == "CRC"

    def test_pilot_case_fau_usd_pocket(self) -> None:
        """Pilot: Fau starts with $2,930 (Equifax + Deel). After subs $43 = $2,887."""
        pocket = _pocket_doc("pocket_fau_usd", "USD", "Fau — dólares", "uid_fau")
        txs = [
            _tx_doc("t1", "2930.00", "USD", "opening_balance"),
            _tx_doc("t2", "43.00", "USD", "expense"),
        ]
        db = _make_db(pocket, txs)
        result = pocket_balance(db, "pocket_fau_usd")
        assert result.amount == Decimal("2887.00")

    def test_pilot_case_mari_crc_pocket(self) -> None:
        """Pilot: Mari starts ₡844,140. Moose ₡17,900 (shared) + school ₡120,000."""
        pocket = _pocket_doc("pocket_mari_crc", "CRC", "Mari — colones", "uid_mari")
        txs = [
            _tx_doc("t1", "844140", "CRC", "opening_balance"),
            _tx_doc("t2", "17900", "CRC", "leisure"),    # Moose
            _tx_doc("t3", "120000", "CRC", "debt_payment"),  # Escuela
        ]
        db = _make_db(pocket, txs)
        result = pocket_balance(db, "pocket_mari_crc")
        assert result.amount == Decimal("706240")

    def test_cross_currency_raises(self) -> None:
        """A CRC pocket must not accept a USD transaction."""
        pocket = _pocket_doc("pocket_mari_crc", "CRC")
        txs = [_tx_doc("t1", "100", "USD", "expense")]  # USD tx in CRC pocket!
        db = _make_db(pocket, txs)
        with pytest.raises(ValueError, match="Currency mismatch"):
            pocket_balance(db, "pocket_mari_crc")

    def test_pocket_not_found_raises(self) -> None:
        db = MagicMock()
        missing = MagicMock()
        missing.exists = False
        db.collection.return_value.document.return_value.get.return_value = missing
        with pytest.raises(ValueError, match="not found"):
            pocket_balance(db, "nonexistent_pocket")


class TestAssertNoCurrencyCross:
    def test_same_currency_passes(self) -> None:
        assert_no_currency_cross("USD", "USD")  # no exception

    def test_same_crc_passes(self) -> None:
        assert_no_currency_cross("CRC", "CRC")

    def test_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="Currency mismatch"):
            assert_no_currency_cross("CRC", "USD")

    def test_mismatch_with_context(self) -> None:
        with pytest.raises(ValueError, match="transaction abc"):
            assert_no_currency_cross("USD", "CRC", context="transaction abc")


class TestValidateTransfer:
    def test_same_currency_valid(self) -> None:
        src = {"currency": "USD"}
        dst = {"currency": "USD"}
        valid, msg = validate_transfer(src, dst, Decimal("500"))
        assert valid is True
        assert msg == ""

    def test_cross_currency_needs_fx(self) -> None:
        src = {"currency": "USD"}
        dst = {"currency": "CRC"}
        valid, msg = validate_transfer(src, dst, Decimal("500"))
        assert valid is False
        assert "FX rate" in msg

    def test_cross_currency_with_fx_valid(self) -> None:
        src = {"currency": "USD"}
        dst = {"currency": "CRC"}
        valid, msg = validate_transfer(src, dst, Decimal("500"), fx_rate=Decimal("470"))
        assert valid is True

    def test_zero_amount_invalid(self) -> None:
        src = {"currency": "CRC"}
        dst = {"currency": "CRC"}
        valid, msg = validate_transfer(src, dst, Decimal("0"))
        assert valid is False
        assert "positive" in msg

    def test_pilot_transfer_fau_to_mari(self) -> None:
        """Pilot: Fau transfers ₡648,000 to Mari's CRC pocket monthly."""
        src = {"currency": "CRC"}  # Fau's CRC pocket
        dst = {"currency": "CRC"}  # Mari's CRC pocket
        valid, msg = validate_transfer(src, dst, Decimal("648000"))
        assert valid is True

    def test_pilot_transfer_usd_to_crc_with_fx(self) -> None:
        """Pilot: Fau USD → Mari CRC; needs FX rate."""
        src = {"currency": "USD"}
        dst = {"currency": "CRC"}
        valid, msg = validate_transfer(src, dst, Decimal("1000"), fx_rate=Decimal("470"))
        assert valid is True
