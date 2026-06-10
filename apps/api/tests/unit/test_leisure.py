"""Unit tests for app.core.leisure — pure, mocked Firestore."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.core.leisure import leisure_status

# ── Helpers ───────────────────────────────────────────────────────────────────

HH_ID = "hh_fau_mari"
TODAY = date(2026, 6, 9)
MONTH = "2026-06"


def _make_doc(doc_id: str, data: dict, exists: bool = True) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id
    doc.exists = exists
    doc.to_dict.return_value = data
    return doc


def _make_db(
    *,
    pockets: list[dict],          # [{"id": ..., "ownerUid": ..., "householdId": ...}]
    budgets: list[dict],          # leisureBudgets docs
    txs: list[dict],              # transactions
    members: list[str] | None = None,
) -> MagicMock:
    """Build a Firestore mock for leisure_status."""
    members = members or ["uid_fau", "uid_mari"]

    hh_doc = _make_doc(HH_ID, {"members": members})

    pocket_docs = [_make_doc(p.pop("id"), p) for p in [dict(p) for p in pockets]]
    budget_docs = [_make_doc(f"lb_{i}", b) for i, b in enumerate(budgets)]
    tx_docs = [_make_doc(f"tx_{i}", t) for i, t in enumerate(txs)]

    households_col = MagicMock()
    households_col.document.return_value.get.return_value = hh_doc

    pockets_col = MagicMock()
    pockets_col.where.return_value.stream.return_value = iter(pocket_docs)

    budgets_col = MagicMock()
    budgets_col.where.return_value.stream.return_value = iter(budget_docs)

    txs_col = MagicMock()
    txs_col.where.return_value.stream.return_value = iter(tx_docs)

    db = MagicMock()
    db.collection.side_effect = lambda name: {
        "households": households_col,
        "pockets": pockets_col,
        "leisureBudgets": budgets_col,
        "transactions": txs_col,
    }.get(name, MagicMock())
    return db


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestLeisureStatusEmpty:
    def test_no_budgets_returns_empty_individual_and_no_household(self) -> None:
        db = _make_db(pockets=[], budgets=[], txs=[])
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert result.household_id == HH_ID
        assert result.individual == []
        assert result.household_budget is None

    def test_period_covers_full_month(self) -> None:
        db = _make_db(pockets=[], budgets=[], txs=[])
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert result.period_start == date(2026, 6, 1)
        assert result.period_end == date(2026, 6, 30)


class TestIndividualBudgets:
    def test_zero_spent_when_no_txs(self) -> None:
        db = _make_db(
            pockets=[
                {"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID},
            ],
            budgets=[
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000"},
            ],
            txs=[],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert len(result.individual) == 1
        entry = result.individual[0]
        assert entry["uid"] == "uid_mari"
        assert entry["monthly_cap"] == Decimal("150000")
        assert entry["spent"] == Decimal("0")
        assert entry["available"] == Decimal("150000")

    def test_pilot_mari_moose_17900(self) -> None:
        """Pilot: Mari spent ₡17,900 on Moose (family outing) from her CRC pocket.
        Individual cap ₡150,000. Remaining: ₡132,100.
        """
        db = _make_db(
            pockets=[
                {"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID},
                {"id": "pocket_fau_usd", "ownerUid": "uid_fau", "householdId": HH_ID},
            ],
            budgets=[
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": "pocket_mari_crc",
                 "date": "2026-06-07", "amount": "17900", "currency": "CRC",
                 "type": "leisure", "concept": "Moose — salida familiar"},
            ],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert len(result.individual) == 1
        entry = result.individual[0]
        assert entry["uid"] == "uid_mari"
        assert entry["spent"] == Decimal("17900")
        assert entry["available"] == Decimal("132100")

    def test_two_individual_budgets(self) -> None:
        """Both Fau and Mari have individual leisure budgets; each tracks independently."""
        db = _make_db(
            pockets=[
                {"id": "pocket_fau_usd", "ownerUid": "uid_fau", "householdId": HH_ID},
                {"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID},
            ],
            budgets=[
                {"type": "individual", "ownerUid": "uid_fau", "householdId": HH_ID,
                 "monthlyCap": "200"},
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": "pocket_fau_usd",
                 "date": "2026-06-10", "amount": "50", "currency": "USD",
                 "type": "leisure", "concept": "Netflix"},
                {"householdId": HH_ID, "pocketId": "pocket_mari_crc",
                 "date": "2026-06-07", "amount": "17900", "currency": "CRC",
                 "type": "leisure", "concept": "Moose"},
            ],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        by_uid = {e["uid"]: e for e in result.individual}
        assert by_uid["uid_fau"]["spent"] == Decimal("50")
        assert by_uid["uid_fau"]["available"] == Decimal("150")
        assert by_uid["uid_mari"]["spent"] == Decimal("17900")
        assert by_uid["uid_mari"]["available"] == Decimal("132100")

    def test_only_this_month_txs_count(self) -> None:
        """July transactions must not appear in June leisure status."""
        db = _make_db(
            pockets=[
                {"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID},
            ],
            budgets=[
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000"},
            ],
            txs=[
                # June tx — should count
                {"householdId": HH_ID, "pocketId": "pocket_mari_crc",
                 "date": "2026-06-07", "amount": "17900", "currency": "CRC", "type": "leisure"},
                # July tx — must NOT count
                {"householdId": HH_ID, "pocketId": "pocket_mari_crc",
                 "date": "2026-07-05", "amount": "50000", "currency": "CRC", "type": "leisure"},
            ],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert result.individual[0]["spent"] == Decimal("17900")

    def test_non_leisure_txs_ignored(self) -> None:
        """Expense-type transactions don't count towards leisure budget."""
        db = _make_db(
            pockets=[
                {"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID},
            ],
            budgets=[
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": "pocket_mari_crc",
                 "date": "2026-06-07", "amount": "120000", "currency": "CRC",
                 "type": "expense", "concept": "Escuela"},
            ],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert result.individual[0]["spent"] == Decimal("0")

    def test_weekly_cap_included_when_set(self) -> None:
        db = _make_db(
            pockets=[{"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID}],
            budgets=[
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000", "weeklyCap": "40000"},
            ],
            txs=[],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert result.individual[0].get("weekly_cap") == Decimal("40000")

    def test_weekly_cap_absent_when_not_set(self) -> None:
        db = _make_db(
            pockets=[{"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID}],
            budgets=[
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000"},
            ],
            txs=[],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert "weekly_cap" not in result.individual[0]


class TestHouseholdBudget:
    def test_household_budget_split_50_50(self) -> None:
        """Household leisure budget ₡300,000 / 2 members = ₡150,000 per member."""
        db = _make_db(
            pockets=[
                {"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID},
            ],
            budgets=[
                {"type": "household", "householdId": HH_ID, "monthlyCap": "300000"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": "pocket_mari_crc",
                 "date": "2026-06-07", "amount": "17900", "currency": "CRC",
                 "type": "leisure", "concept": "Moose — salida familiar"},
            ],
            members=["uid_fau", "uid_mari"],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert result.household_budget is not None
        hb = result.household_budget
        assert hb["monthly_cap"] == Decimal("300000")
        assert hb["per_member_cap"] == Decimal("150000")  # 300,000 / 2
        assert hb["spent"] == Decimal("17900")
        assert hb["available"] == Decimal("282100")

    def test_household_budget_three_members(self) -> None:
        """3-member household splits cap by 3."""
        db = _make_db(
            pockets=[],
            budgets=[
                {"type": "household", "householdId": HH_ID, "monthlyCap": "300000"},
            ],
            txs=[],
            members=["u1", "u2", "u3"],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert result.household_budget is not None
        assert result.household_budget["per_member_cap"] == Decimal("100000")

    def test_individual_and_household_coexist(self) -> None:
        """Individual budget and household budget can coexist in the same response."""
        db = _make_db(
            pockets=[
                {"id": "pocket_mari_crc", "ownerUid": "uid_mari", "householdId": HH_ID},
            ],
            budgets=[
                {"type": "individual", "ownerUid": "uid_mari", "householdId": HH_ID,
                 "monthlyCap": "150000"},
                {"type": "household", "householdId": HH_ID, "monthlyCap": "300000"},
            ],
            txs=[],
        )
        with patch("app.core.leisure.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = leisure_status(db, HH_ID)
        assert len(result.individual) == 1
        assert result.household_budget is not None
