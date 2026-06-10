"""Unit tests for app.core.goals — pure math + Firestore-backed."""
from __future__ import annotations

from datetime import date
from datetime import date as real_date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.core.goals import goal_progress, goal_status

HH_ID = "hh_fau_mari"
TODAY = date(2026, 6, 9)


def _make_doc(doc_id: str, data: dict, exists: bool = True) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id
    doc.exists = exists
    doc.to_dict.return_value = data
    return doc


def _make_db(*, goals: list[dict]) -> MagicMock:
    """Build a Firestore mock for goal_status."""
    goal_docs = [_make_doc(f"goal_{i}", g) for i, g in enumerate(goals)]
    goals_col = MagicMock()
    goals_col.where.return_value.stream.return_value = iter(goal_docs)

    db = MagicMock()
    db.collection.side_effect = lambda name: goals_col if name == "goals" else MagicMock()
    return db


# ── Pure math ─────────────────────────────────────────────────────────────────

class TestGoalProgress:
    def test_zero_saved(self) -> None:
        result = goal_progress(Decimal("0"), Decimal("1000"))
        assert result["pct"] == Decimal("0.0")
        assert result["remaining"] == Decimal("1000")
        assert result["monthly_needed"] is None

    def test_fully_saved(self) -> None:
        result = goal_progress(Decimal("1000"), Decimal("1000"))
        assert result["pct"] == Decimal("100.0")
        assert result["remaining"] == Decimal("0")

    def test_monthly_needed_with_target_date(self) -> None:
        """6 months away, $600 remaining → $100/month needed."""
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY  # June 2026
            result = goal_progress(
                Decimal("400"),
                Decimal("1000"),
                target_date=date(2026, 12, 1),  # 6 months away
            )
        assert result["monthly_needed"] == Decimal("100.00")

    def test_monthly_needed_none_when_no_target_date(self) -> None:
        result = goal_progress(Decimal("0"), Decimal("1000"), target_date=None)
        assert result["monthly_needed"] is None

    def test_monthly_needed_none_when_already_reached(self) -> None:
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = goal_progress(
                Decimal("1000"),
                Decimal("1000"),
                target_date=date(2026, 12, 1),
            )
        assert result["monthly_needed"] is None

    def test_pilot_chile_vacation_goal(self) -> None:
        """Pilot: Chile trip goal $1,000 USD, saved $0, 6 months away → $167/month."""
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = goal_progress(
                Decimal("0"),
                Decimal("1000"),
                target_date=date(2026, 12, 1),
            )
        assert result["remaining"] == Decimal("1000")
        # 6 months: $1,000 / 6 = $166.67 → rounded $166.67
        assert result["monthly_needed"] == pytest.approx(Decimal("166.67"), abs=Decimal("0.01"))

    def test_pct_rounds_to_one_decimal(self) -> None:
        result = goal_progress(Decimal("1"), Decimal("3"))
        assert result["pct"] == Decimal("33.3")


# ── Firestore-backed ──────────────────────────────────────────────────────────

class TestGoalStatus:
    def test_no_goals_returns_empty_list(self) -> None:
        db = _make_db(goals=[])
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = goal_status(db, HH_ID)
        assert result.household_id == HH_ID
        assert result.goals == []

    def test_single_goal_no_target_date(self) -> None:
        db = _make_db(goals=[{
            "householdId": HH_ID,
            "name": "Fondo vacaciones",
            "target": "1000",
            "saved": "250",
            "currency": "USD",
        }])
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = goal_status(db, HH_ID)
        assert len(result.goals) == 1
        g = result.goals[0]
        assert g.name == "Fondo vacaciones"
        assert g.target == Decimal("1000")
        assert g.saved == Decimal("250")
        assert g.remaining == Decimal("750")
        assert g.pct == Decimal("25.0")
        assert g.monthly_needed is None
        assert g.currency.value == "USD"

    def test_pilot_chile_goal_with_target_date(self) -> None:
        """Pilot: Chile vacation $1,000, saved $0, target Dec 2026 → $166.67/month."""
        db = _make_db(goals=[{
            "householdId": HH_ID,
            "name": "Viaje Chile",
            "target": "1000",
            "saved": "0",
            "currency": "USD",
            "targetDate": "2026-12-01",
        }])
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY
            mock_date.fromisoformat.side_effect = real_date.fromisoformat
            result = goal_status(db, HH_ID)
        g = result.goals[0]
        assert g.name == "Viaje Chile"
        assert g.monthly_needed == pytest.approx(Decimal("166.67"), abs=Decimal("0.01"))
        assert g.target_date == date(2026, 12, 1)

    def test_multiple_goals_all_returned(self) -> None:
        db = _make_db(goals=[
            {"householdId": HH_ID, "name": "Carro", "target": "5000",
             "saved": "1000", "currency": "USD"},
            {"householdId": HH_ID, "name": "Vacaciones", "target": "1000",
             "saved": "500", "currency": "USD"},
        ])
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = goal_status(db, HH_ID)
        assert len(result.goals) == 2
        names = {g.name for g in result.goals}
        assert names == {"Carro", "Vacaciones"}

    def test_completed_goal_zero_remaining(self) -> None:
        db = _make_db(goals=[{
            "householdId": HH_ID,
            "name": "Escudo",
            "target": "200000",
            "saved": "200000",
            "currency": "CRC",
        }])
        with patch("app.core.goals.date") as mock_date:
            mock_date.today.return_value = TODAY
            result = goal_status(db, HH_ID)
        g = result.goals[0]
        assert g.remaining == Decimal("0")
        assert g.pct == Decimal("100.0")
        assert g.monthly_needed is None
