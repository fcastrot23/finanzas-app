"""Component tests for Fase 2 endpoints.

Endpoints covered:
  POST /households/{id}/simulate                  green / amber / red
  GET  /households/{id}/leisure/status            empty / with spending
  POST /households/{id}/plans/{id}/propose        draft → proposed
  POST /households/{id}/plans/{id}/approve        proposed → active (all-members vote)
  POST /households/{id}/plans/{id}/approve        archive old active plan on new activation
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.security.auth import get_current_uid
from main import app

# ── Pilot constants ───────────────────────────────────────────────────────────

HH_ID = "hh_fau_mari"
FAU_UID = "uid_fau"
MARI_UID = "uid_mari"
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


def _household_doc(members: list[str] | None = None) -> MagicMock:
    return _make_doc(HH_ID, {"members": members or [FAU_UID, MARI_UID], "name": "Fau & Mari"})


@contextmanager
def _patch_db(mock_db: MagicMock):
    with patch("app.db.firestore.get_db", return_value=mock_db):
        yield


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    app.dependency_overrides[get_current_uid] = lambda: FAU_UID
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── POST /simulate ────────────────────────────────────────────────────────────

class TestSimulateEndpoint:
    """POST /households/{id}/simulate → SimulateResponse."""

    def _make_simulate_db(
        self,
        *,
        pocket_currency: str = "USD",
        balance_amount: str = "2000",
        plan_lines: list[dict] | None = None,
    ) -> MagicMock:
        plan_lines = plan_lines or []

        # pockets
        pocket_doc = _make_doc(POCKET_USD, {"currency": pocket_currency, "name": "Fau USD"})
        pockets_col = MagicMock()
        pockets_col.document.return_value.get.return_value = pocket_doc

        # transactions: pocketId query → balance txs; householdId query → paid txs
        balance_tx = _make_doc("btx_0", {
            "pocketId": POCKET_USD, "amount": balance_amount,
            "currency": pocket_currency, "type": "opening_balance",
        })
        txs_col = MagicMock()
        txs_col.where.side_effect = lambda field, *_: MagicMock(
            stream=MagicMock(return_value=iter([balance_tx] if field == "pocketId" else []))
        )

        # plans
        plan_doc = _make_doc("plan_1", {"householdId": HH_ID, "status": "active"})
        line_docs = [_make_doc(f"line_{i}", ln) for i, ln in enumerate(plan_lines)]
        second_where = MagicMock()
        second_where.stream.return_value = iter([plan_doc])
        first_where = MagicMock()
        first_where.where.return_value = second_where
        plans_col = MagicMock()
        plans_col.where.return_value = first_where
        lines_col = MagicMock()
        lines_col.stream.return_value = iter(line_docs)
        plans_col.document.return_value.collection.return_value = lines_col

        hh_col = MagicMock()
        hh_col.document.return_value.get.return_value = _household_doc()

        db = MagicMock()
        db.collection.side_effect = lambda name: {
            "households": hh_col,
            "pockets": pockets_col,
            "transactions": txs_col,
            "plans": plans_col,
        }.get(name, MagicMock())
        return db

    def test_green_returns_200_with_traffic_light(self, client: TestClient) -> None:
        """$2,000 balance, $0 obligations, $500 proposal → green."""
        db = self._make_simulate_db(balance_amount="2000")
        with _patch_db(db):
            resp = client.post(
                f"/households/{HH_ID}/simulate",
                json={
                    "pocket_id": POCKET_USD,
                    "amount": "500",
                    "currency": "USD",
                    "concept": "Cena restaurante",
                    "proposed_date": "2026-06-20",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["light"] == "green"
        assert body["feasible"] is True
        assert body["sacrifice"] is None

    def test_amber_pilot_vacation(self, client: TestClient) -> None:
        """Pilot: $1,000 vacation with $1,200 balance, $600 committed, $800 deferrable → amber."""
        db = self._make_simulate_db(
            balance_amount="1200",
            plan_lines=[
                {"pocketId": POCKET_USD, "date": "2026-06-01", "amount": "600",
                 "currency": "USD", "type": "expense", "concept": "Subs"},
                {"pocketId": POCKET_USD, "date": "2026-06-06", "amount": "800",
                 "currency": "USD", "type": "debt", "concept": "BAC tarjeta"},
            ],
        )
        with _patch_db(db):
            resp = client.post(
                f"/households/{HH_ID}/simulate",
                json={
                    "pocket_id": POCKET_USD,
                    "amount": "1000",
                    "currency": "USD",
                    "concept": "Vacaciones julio",
                    "proposed_date": "2026-06-20",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["light"] == "amber"
        assert body["feasible"] is True
        assert body["sacrifice"] is not None
        assert "BAC tarjeta" in body["sacrifice"]

    def test_red_insufficient_funds(self, client: TestClient) -> None:
        """$100 balance, $1,000 proposal → red."""
        db = self._make_simulate_db(balance_amount="100")
        with _patch_db(db):
            resp = client.post(
                f"/households/{HH_ID}/simulate",
                json={
                    "pocket_id": POCKET_USD,
                    "amount": "1000",
                    "currency": "USD",
                    "concept": "Algo caro",
                    "proposed_date": "2026-06-20",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["light"] == "red"
        assert body["feasible"] is False

    def test_simulate_requires_auth(self) -> None:
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.post(
            f"/households/{HH_ID}/simulate",
            json={"pocket_id": POCKET_USD, "amount": "100", "currency": "USD",
                  "concept": "test", "proposed_date": "2026-06-20"},
        )
        assert resp.status_code == 401

    def test_simulate_response_has_required_fields(self, client: TestClient) -> None:
        db = self._make_simulate_db(balance_amount="2000")
        with _patch_db(db):
            resp = client.post(
                f"/households/{HH_ID}/simulate",
                json={"pocket_id": POCKET_USD, "amount": "100", "currency": "USD",
                      "concept": "test", "proposed_date": "2026-06-20"},
            )
        body = resp.json()
        for field in ("light", "feasible", "detail"):
            assert field in body, f"Missing field: {field}"


# ── GET /leisure/status ───────────────────────────────────────────────────────

class TestLeisureStatusEndpoint:
    """GET /households/{id}/leisure/status → LeisureStatus."""

    def _make_leisure_db(
        self,
        *,
        budgets: list[dict] | None = None,
        txs: list[dict] | None = None,
    ) -> MagicMock:
        budgets = budgets or []
        txs = txs or []

        hh_col = MagicMock()
        hh_col.document.return_value.get.return_value = _household_doc()

        pockets_col = MagicMock()
        pockets_col.where.return_value.stream.return_value = iter([
            _make_doc(POCKET_CRC, {"ownerUid": MARI_UID, "householdId": HH_ID, "currency": "CRC"}),
        ])

        budgets_col = MagicMock()
        budgets_col.where.return_value.stream.return_value = iter([
            _make_doc(f"lb_{i}", b) for i, b in enumerate(budgets)
        ])

        txs_col = MagicMock()
        txs_col.where.return_value.stream.return_value = iter([
            _make_doc(f"tx_{i}", t) for i, t in enumerate(txs)
        ])

        db = MagicMock()
        db.collection.side_effect = lambda name: {
            "households": hh_col,
            "pockets": pockets_col,
            "leisureBudgets": budgets_col,
            "transactions": txs_col,
        }.get(name, MagicMock())
        return db

    def test_returns_200_with_schema(self, client: TestClient) -> None:
        with patch("app.core.leisure.date") as mock_date:
            from datetime import date
            mock_date.today.return_value = date(2026, 6, 9)
            with _patch_db(self._make_leisure_db()):
                resp = client.get(f"/households/{HH_ID}/leisure/status")
        assert resp.status_code == 200
        body = resp.json()
        assert "household_id" in body
        assert "individual" in body
        assert "period_start" in body
        assert "period_end" in body

    def test_empty_individual_when_no_budgets(self, client: TestClient) -> None:
        with patch("app.core.leisure.date") as mock_date:
            from datetime import date
            mock_date.today.return_value = date(2026, 6, 9)
            with _patch_db(self._make_leisure_db(budgets=[])):
                resp = client.get(f"/households/{HH_ID}/leisure/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["individual"] == []
        assert body["household_budget"] is None

    def test_pilot_mari_moose_shows_spent(self, client: TestClient) -> None:
        """Pilot: Mari spent ₡17,900 on Moose → shows in individual entry."""
        db = self._make_leisure_db(
            budgets=[
                {"type": "individual", "ownerUid": MARI_UID, "householdId": HH_ID,
                 "monthlyCap": "150000"},
            ],
            txs=[
                {"householdId": HH_ID, "pocketId": POCKET_CRC,
                 "date": "2026-06-07", "amount": "17900", "currency": "CRC",
                 "type": "leisure", "concept": "Moose"},
            ],
        )
        with patch("app.core.leisure.date") as mock_date:
            from datetime import date
            mock_date.today.return_value = date(2026, 6, 9)
            with _patch_db(db):
                resp = client.get(f"/households/{HH_ID}/leisure/status")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["individual"]) == 1
        entry = body["individual"][0]
        assert entry["uid"] == MARI_UID
        assert str(entry["spent"]) == "17900"

    def test_leisure_status_requires_auth(self) -> None:
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.get(f"/households/{HH_ID}/leisure/status")
        assert resp.status_code == 401


# ── Plan approval flow ────────────────────────────────────────────────────────

class TestPlanApprovalFlow:
    """POST /plans/{id}/propose and /plans/{id}/approve — state machine."""

    def _plan_doc(self, plan_id: str, status: str, approvals: dict | None = None) -> MagicMock:
        doc = _make_doc(plan_id, {
            "householdId": HH_ID,
            "status": status,
            "version": 1,
            "period": {"from": "2026-06-01", "to": "2026-08-31"},
            "approvals": approvals or {},
        })
        # lines subcollection
        doc.reference.collection.return_value.stream.return_value = iter([])
        return doc

    def _make_plan_db(self, plan_doc: MagicMock) -> MagicMock:
        updated_data: dict = {}

        def _update(data: dict) -> None:
            updated_data.update(data)
            merged = {**plan_doc.to_dict.return_value, **updated_data}
            plan_doc.to_dict.return_value = merged

        plan_ref = MagicMock()
        plan_ref.get.return_value = plan_doc
        plan_ref.update.side_effect = _update
        plan_ref.collection.return_value.stream.return_value = iter([])

        plans_col = MagicMock()
        plans_col.document.return_value = plan_ref
        # Stub chained where().where().stream() for archive-previous-plan step
        plans_col.where.return_value.where.return_value.stream.return_value = iter([])

        hh_col = MagicMock()
        hh_col.document.return_value.get.return_value = _household_doc()

        db = MagicMock()
        db.collection.side_effect = lambda name: {
            "households": hh_col,
            "plans": plans_col,
        }.get(name, MagicMock())
        return db

    def test_propose_transitions_draft_to_proposed(self, client: TestClient) -> None:
        plan_doc = self._plan_doc("plan_1", "draft")
        db = self._make_plan_db(plan_doc)
        with _patch_db(db):
            resp = client.post(f"/households/{HH_ID}/plans/plan_1/propose")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "proposed"

    def test_approve_with_one_member_stays_proposed(self, client: TestClient) -> None:
        """One approval from a 2-member household → plan stays proposed (not yet active)."""
        plan_doc = self._plan_doc("plan_1", "proposed")
        db = self._make_plan_db(plan_doc)
        with _patch_db(db):
            resp = client.post(
                f"/households/{HH_ID}/plans/plan_1/approve",
                json={"uid": FAU_UID, "approved": True, "reason": "LGTM"},
            )
        assert resp.status_code == 200
        body = resp.json()
        # Only Fau approved; Mari hasn't yet → still proposed
        assert body["status"] == "proposed"
        assert body["approvals"][FAU_UID] is True

    def test_approve_all_members_activates_plan(self, client: TestClient) -> None:
        """All members approved → plan becomes active."""
        # Pre-set Fau's approval so Mari's vote completes the set
        plan_doc = self._plan_doc("plan_1", "proposed", approvals={FAU_UID: True})
        db = self._make_plan_db(plan_doc)
        app.dependency_overrides[get_current_uid] = lambda: MARI_UID
        with _patch_db(db):
            resp = client.post(
                f"/households/{HH_ID}/plans/plan_1/approve",
                json={"uid": MARI_UID, "approved": True, "reason": "De acuerdo"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "active"

    def test_approve_404_for_nonexistent_plan(self, client: TestClient) -> None:
        no_plan_doc = _make_doc("nope", {}, exists=False)
        db = self._make_plan_db(no_plan_doc)
        with _patch_db(db):
            resp = client.post(
                f"/households/{HH_ID}/plans/nope/approve",
                json={"uid": FAU_UID, "approved": True, "reason": "x"},
            )
        assert resp.status_code == 404

    def test_propose_404_for_nonexistent_plan(self, client: TestClient) -> None:
        no_plan_doc = _make_doc("nope", {}, exists=False)
        db = self._make_plan_db(no_plan_doc)
        with _patch_db(db):
            resp = client.post(f"/households/{HH_ID}/plans/nope/propose")
        assert resp.status_code == 404
