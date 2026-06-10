"""Unit tests for app.core.simulation (pure, no I/O)."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock


def _make_db_stub(household_members: list[str]) -> MagicMock:
    """Return a minimal Firestore stub for simulation tests."""
    db = MagicMock()
    hh_doc = MagicMock()
    hh_doc.exists = True
    hh_doc.to_dict.return_value = {"members": household_members, "fxRef": "470"}
    db.collection.return_value.document.return_value.get.return_value = hh_doc
    return db


def test_simulate_returns_response_shape() -> None:
    """Stub smoke-test: simulate_expense returns a valid SimulateResponse."""
    from app.core.simulation import simulate_expense
    from app.models.schemas import SimulateRequest, TrafficLight

    db = _make_db_stub(["uid_fau", "uid_mari"])
    req = SimulateRequest(
        pocket_id="pocket_fau_usd",
        amount=Decimal("1000"),
        currency="USD",
        concept="Vacaciones julio",
        proposed_date=__import__("datetime").date(2026, 7, 15),
    )
    result = simulate_expense(db, "hh_fau_mari", req)
    assert result.light in list(TrafficLight)
    assert isinstance(result.feasible, bool)
    assert isinstance(result.detail, str)


def test_vacation_1000_pausing_avalanche_is_feasible() -> None:
    """Pilot case: ~$1,000 July trip, pausing avalanche, keeps emergency fund.

    With Hyatt income ($4,295) + Equifax ($4,037/month) the household has
    sufficient margin to fund the trip by pausing the extra avalanche payment
    for one month. The stub currently returns green/feasible; the real simulation
    logic in API-2.1 will validate the full trade-off.
    """
    from app.core.simulation import simulate_expense
    from app.models.schemas import SimulateRequest

    db = _make_db_stub(["uid_fau", "uid_mari"])
    req = SimulateRequest(
        pocket_id="pocket_fau_usd",
        amount=Decimal("1000"),
        currency="USD",
        concept="Vacaciones julio — viaje familia",
        proposed_date=__import__("datetime").date(2026, 7, 15),
    )
    result = simulate_expense(db, "hh_fau_mari", req)
    # The stub is green; once API-2.1 is real, this assertion will validate the trade-off.
    assert result.feasible is True
