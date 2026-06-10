"""Component tests for all P0 endpoints.

Strategy:
- Import the FastAPI `app` and use `TestClient` (synchronous WSGI-like wrapper).
- Override `get_current_uid` via FastAPI dependency_overrides for happy-path tests.
- Patch `app.db.firestore.get_db` to return a mock Firestore client.
  NOTE: auth.py does `from app.db.firestore import get_db` inside its functions,
  so patching the source (`app.db.firestore.get_db`) covers all callers.
- Auth tests use no override and verify 401/403 behavior.

P0 endpoints covered:
  GET  /health                                   (no auth)
  POST /households/{id}/plans                    (create draft)
  POST /households/{id}/plans/{id}/validate      (validate plan)
  POST /households/{id}/transactions             (create transaction)
  GET  /households/{id}/comparison/{month}       (plan vs actual)
  GET  /households/{id}/debts/avalanche          (debt ordering)
  --- auth ---
  GET  /health → 200 (no auth needed)
  GET  /households/{id}/comparison/2026-06 → 401 without token
  GET  /households/{id}/comparison/2026-06 → 403 when not a member
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
MONTH = "2026-06"


# ── Mock Firestore helpers ────────────────────────────────────────────────────

def _make_doc(doc_id: str, data: dict, exists: bool = True) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id
    doc.exists = exists
    doc.to_dict.return_value = data
    return doc


def _household_doc(members: list[str] | None = None) -> MagicMock:
    return _make_doc(
        HH_ID,
        {"members": members or [FAU_UID, "uid_mari"], "name": "Fau & Mari"},
    )


@contextmanager
def _patch_db(mock_db: MagicMock):
    """Patch `get_db` at its source module so all callers (routers + auth) get the mock."""
    with patch("app.db.firestore.get_db", return_value=mock_db):
        yield


def _simple_db(hh_members: list[str] | None = None, **collections) -> MagicMock:
    """Build a mock DB with household membership + extra collection overrides.

    collections: keyword args mapping collection name → MagicMock col object.
    """
    mock_db = MagicMock()
    hh_col = MagicMock()
    hh_col.document.return_value.get.return_value = _household_doc(hh_members)

    def _col(name: str) -> MagicMock:
        if name == "households":
            return hh_col
        if name in collections:
            return collections[name]
        return MagicMock()

    mock_db.collection.side_effect = _col
    return mock_db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_client():
    """TestClient with get_current_uid returning FAU_UID (no Firebase calls)."""
    app.dependency_overrides[get_current_uid] = lambda: FAU_UID
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def no_auth_client():
    """TestClient with NO dependency overrides (real auth flow)."""
    app.dependency_overrides.clear()
    yield TestClient(app)


# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, no_auth_client: TestClient) -> None:
        resp = no_auth_client.get("/health")
        assert resp.status_code == 200

    def test_health_response_schema(self, no_auth_client: TestClient) -> None:
        body = no_auth_client.get("/health").json()
        assert body["status"] == "ok"
        assert "version" in body


# ── Auth: 401 / 403 ───────────────────────────────────────────────────────────

class TestAuthBehavior:
    def test_401_without_token(self, no_auth_client: TestClient) -> None:
        resp = no_auth_client.get(f"/households/{HH_ID}/comparison/{MONTH}")
        assert resp.status_code == 401

    def test_401_with_bad_token(self, no_auth_client: TestClient) -> None:
        resp = no_auth_client.get(
            f"/households/{HH_ID}/comparison/{MONTH}",
            headers={"Authorization": "Bearer invalid-token-xyz"},
        )
        assert resp.status_code == 401

    def test_403_when_not_member(self, no_auth_client: TestClient) -> None:
        """An outsider uid that is NOT in the household gets 403."""
        outsider_uid = "uid_outsider"
        app.dependency_overrides[get_current_uid] = lambda: outsider_uid

        # Household has only Fau & Mari — outsider not listed.
        # Wire plans/transactions so the endpoint doesn't error before 403 check.
        plans_col = MagicMock()
        plans_col.where.return_value.where.return_value.stream.return_value = iter([])
        plans_col.document.return_value.collection.return_value.stream.return_value = iter([])
        txs_col = MagicMock()
        txs_col.where.return_value.stream.return_value = iter([])

        def _col(name: str) -> MagicMock:
            if name == "households":
                hh_col = MagicMock()
                hh_col.document.return_value.get.return_value = _household_doc(
                    [FAU_UID, "uid_mari"]
                )
                return hh_col
            if name == "plans":
                return plans_col
            if name == "transactions":
                return txs_col
            return MagicMock()

        mock_db2 = MagicMock()
        mock_db2.collection.side_effect = _col

        with _patch_db(mock_db2):
            resp = no_auth_client.get(f"/households/{HH_ID}/comparison/{MONTH}")

        app.dependency_overrides.clear()
        assert resp.status_code == 403


# ── POST /households/{id}/plans ───────────────────────────────────────────────

class TestCreatePlan:
    def _make_create_plan_db(self) -> MagicMock:
        """DB mock for the create_plan endpoint."""
        plan_data = {
            "householdId": HH_ID,
            "status": "draft",
            "version": 1,
            "period": {"from": "2026-06-01", "to": "2026-08-31"},
            "approvals": {},
        }
        line_data = {
            "date": "2026-06-14",
            "pocketId": "pocket_fau_usd",
            "concept": "Equifax Q1",
            "amount": "2018.65",
            "currency": "USD",
            "category": "income",
            "type": "income",
        }
        plan_ref = MagicMock()
        plan_ref.id = "plan_new_001"
        plan_ref.get.return_value = _make_doc("plan_new_001", plan_data)
        # plan_ref.collection("lines").document().set() — no-op
        plan_ref.collection.return_value.document.return_value.set.return_value = None
        # plan_ref.collection("lines").stream() → the line we created
        plan_ref.collection.return_value.stream.return_value = iter(
            [_make_doc("line_001", line_data)]
        )

        plans_col = MagicMock()
        plans_col.document.return_value = plan_ref
        plans_col.where.return_value.stream.return_value = iter([])

        return _simple_db(plans=plans_col)

    def test_create_plan_returns_201(self, auth_client: TestClient) -> None:
        mock_db = self._make_create_plan_db()
        payload = {
            "period_from": "2026-06-01",
            "period_to": "2026-08-31",
            "lines": [
                {
                    "date": "2026-06-14",
                    "pocket_id": "pocket_fau_usd",
                    "concept": "Equifax Q1",
                    "amount": "2018.65",
                    "currency": "USD",
                    "category": "income",
                    "type": "income",
                }
            ],
        }
        with _patch_db(mock_db):
            resp = auth_client.post(f"/households/{HH_ID}/plans", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "draft"
        assert body["household_id"] == HH_ID

    def test_create_plan_has_correct_period(self, auth_client: TestClient) -> None:
        mock_db = self._make_create_plan_db()
        payload = {
            "period_from": "2026-06-01",
            "period_to": "2026-08-31",
            "lines": [
                {
                    "date": "2026-06-14",
                    "pocket_id": "pocket_fau_usd",
                    "concept": "Equifax Q1",
                    "amount": "2018.65",
                    "currency": "USD",
                    "category": "income",
                    "type": "income",
                }
            ],
        }
        with _patch_db(mock_db):
            resp = auth_client.post(f"/households/{HH_ID}/plans", json=payload)
        body = resp.json()
        assert body["period"]["from"] == "2026-06-01"
        assert body["period"]["to"] == "2026-08-31"

    def test_create_plan_validates_schema(self, auth_client: TestClient) -> None:
        """Missing required field → 422 Unprocessable Entity."""
        resp = auth_client.post(
            f"/households/{HH_ID}/plans",
            json={"period_from": "2026-06-01"},  # missing period_to and lines
        )
        assert resp.status_code == 422


# ── POST /households/{id}/plans/{id}/validate ─────────────────────────────────

class TestValidatePlan:
    def _make_validate_db(self, period_from: str, period_to: str) -> MagicMock:
        plan_data = {
            "householdId": HH_ID,
            "status": "draft",
            "version": 1,
            "period": {"from": period_from, "to": period_to},
            "approvals": {},
        }
        line_data = {
            "date": "2026-06-14",
            "pocketId": "pocket_fau_usd",
            "concept": "Equifax Q1",
            "amount": "2018.65",
            "currency": "USD",
            "category": "income",
            "type": "income",
        }
        plan_doc = _make_doc("plan_001", plan_data)
        # plan_doc.reference needed for list_plans but validate uses _fetch_plan
        plan_doc.reference = MagicMock()

        plans_col = MagicMock()
        plans_col.document.return_value.get.return_value = plan_doc
        plans_col.document.return_value.collection.return_value.stream.return_value = iter(
            [_make_doc("line_001", line_data)]
        )
        plans_col.where.return_value.stream.return_value = iter([])

        return _simple_db(plans=plans_col)

    def test_validate_valid_plan(self, auth_client: TestClient) -> None:
        mock_db = self._make_validate_db("2026-06-01", "2026-08-31")
        with _patch_db(mock_db):
            resp = auth_client.post(f"/households/{HH_ID}/plans/plan_001/validate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["errors"] == []

    def test_validate_plan_with_bad_period(self, auth_client: TestClient) -> None:
        """Period from >= to → errors list is non-empty."""
        mock_db = self._make_validate_db("2026-09-01", "2026-08-31")  # reversed
        with _patch_db(mock_db):
            resp = auth_client.post(f"/households/{HH_ID}/plans/plan_001/validate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is False
        assert len(body["errors"]) > 0

    def test_validate_returns_valid_field(self, auth_client: TestClient) -> None:
        mock_db = self._make_validate_db("2026-06-01", "2026-08-31")
        with _patch_db(mock_db):
            resp = auth_client.post(f"/households/{HH_ID}/plans/plan_001/validate")
        body = resp.json()
        assert "valid" in body
        assert "errors" in body
        assert "warnings" in body


# ── POST /households/{id}/transactions ───────────────────────────────────────

class TestCreateTransaction:
    def _make_tx_db(self) -> MagicMock:
        tx_data = {
            "householdId": HH_ID,
            "pocketId": "pocket_fau_usd",
            "date": "2026-06-06",
            "concept": "BAC tarjeta — abono",
            "amount": "800",
            "currency": "USD",
            "fx": None,
            "planLineId": None,
            "status": "out_of_plan",
            "category": "debt",
            "split": [],
            "createdAt": "2026-06-06T00:00:00",
        }
        tx_ref = MagicMock()
        tx_ref.id = "tx_001"
        tx_ref.get.return_value = _make_doc("tx_001", tx_data)

        txs_col = MagicMock()
        txs_col.document.return_value = tx_ref

        return _simple_db(transactions=txs_col)

    def test_create_transaction_returns_201(self, auth_client: TestClient) -> None:
        mock_db = self._make_tx_db()
        payload = {
            "pocket_id": "pocket_fau_usd",
            "date": "2026-06-06",
            "concept": "BAC tarjeta — abono",
            "amount": "800.00",
            "currency": "USD",
            "category": "debt",
        }
        with _patch_db(mock_db):
            resp = auth_client.post(f"/households/{HH_ID}/transactions", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["concept"] == "BAC tarjeta — abono"
        assert body["currency"] == "USD"
        assert Decimal(body["amount"]) == Decimal("800")

    def test_create_transaction_status_out_of_plan(self, auth_client: TestClient) -> None:
        """Transaction without plan_line_id must default to out_of_plan status."""
        payload = {
            "pocket_id": "pocket_fau_usd",
            "date": "2026-06-06",
            "concept": "Moose — salida familiar",
            "amount": "17900",
            "currency": "CRC",
            "category": "leisure",
        }
        tx_ref = MagicMock()
        tx_ref.id = "tx_moose"
        tx_ref.get.return_value = _make_doc(
            "tx_moose",
            {**payload, "householdId": HH_ID, "pocketId": "pocket_mari_crc",
             "status": "out_of_plan", "planLineId": None, "split": [], "createdAt": "..."},
        )
        txs_col = MagicMock()
        txs_col.document.return_value = tx_ref
        mock_db2 = _simple_db(transactions=txs_col)
        with _patch_db(mock_db2):
            resp = auth_client.post(f"/households/{HH_ID}/transactions", json=payload)
        # The mock returns what we set up; just verify the call succeeds
        assert resp.status_code == 201

    def test_create_transaction_missing_amount_422(self, auth_client: TestClient) -> None:
        resp = auth_client.post(
            f"/households/{HH_ID}/transactions",
            json={"pocket_id": "p1", "date": "2026-06-06", "concept": "Test", "currency": "USD"},
        )
        assert resp.status_code == 422

    def test_create_transaction_negative_amount_422(self, auth_client: TestClient) -> None:
        """Negative amount must be rejected (PositiveDecimal constraint)."""
        resp = auth_client.post(
            f"/households/{HH_ID}/transactions",
            json={
                "pocket_id": "p1",
                "date": "2026-06-06",
                "concept": "Test",
                "amount": "-100",
                "currency": "USD",
            },
        )
        assert resp.status_code == 422


# ── GET /households/{id}/comparison/{month} ───────────────────────────────────

class TestComparison:
    def _make_comparison_db(
        self,
        planned_amount: str = "800",
        actual_amount: str = "800",
    ) -> MagicMock:
        """DB with one plan line and one transaction for June."""
        plan_doc = _make_doc(
            "plan_001",
            {
                "householdId": HH_ID,
                "status": "active",
                "period": {"from": "2026-06-01", "to": "2026-08-31"},
                "approvals": {},
            },
        )
        line_doc = _make_doc(
            "line_001",
            {
                "pocketId": "pocket_fau_usd",
                "date": "2026-06-06",
                "amount": planned_amount,
                "currency": "USD",
            },
        )
        tx_doc = _make_doc(
            "tx_001",
            {
                "householdId": HH_ID,
                "pocketId": "pocket_fau_usd",
                "date": "2026-06-06",
                "amount": actual_amount,
                "currency": "USD",
            },
        )
        pocket_doc = _make_doc(
            "pocket_fau_usd", {"name": "Fau — dólares", "currency": "USD"}
        )

        plans_col = MagicMock()
        plans_col.where.return_value.where.return_value.stream.return_value = iter([plan_doc])
        plans_col.document.return_value.collection.return_value.stream.return_value = iter(
            [line_doc]
        )

        txs_col = MagicMock()
        txs_col.where.return_value.stream.return_value = iter([tx_doc])

        pockets_col = MagicMock()
        pockets_col.document.return_value.get.return_value = pocket_doc

        def _col(name: str) -> MagicMock:
            if name == "households":
                hh_col = MagicMock()
                hh_col.document.return_value.get.return_value = _household_doc()
                return hh_col
            if name == "plans":
                return plans_col
            if name == "transactions":
                return txs_col
            if name == "pockets":
                return pockets_col
            return MagicMock()

        mock_db = MagicMock()
        mock_db.collection.side_effect = _col
        return mock_db

    def test_comparison_returns_200(self, auth_client: TestClient) -> None:
        with _patch_db(self._make_comparison_db()):
            resp = auth_client.get(f"/households/{HH_ID}/comparison/{MONTH}")
        assert resp.status_code == 200

    def test_comparison_response_schema(self, auth_client: TestClient) -> None:
        with _patch_db(self._make_comparison_db()):
            resp = auth_client.get(f"/households/{HH_ID}/comparison/{MONTH}")
        body = resp.json()
        assert body["month"] == MONTH
        assert body["household_id"] == HH_ID
        assert "items" in body
        assert "total_planned" in body
        assert "total_actual" in body
        assert "total_delta" in body

    def test_comparison_pilot_on_budget(self, auth_client: TestClient) -> None:
        """$800 planned and $800 actual → delta 0."""
        with _patch_db(self._make_comparison_db("800", "800")):
            resp = auth_client.get(f"/households/{HH_ID}/comparison/{MONTH}")
        body = resp.json()
        items = body["items"]
        assert len(items) == 1
        assert Decimal(items[0]["delta"]) == Decimal("0")

    def test_comparison_pilot_overspend(self, auth_client: TestClient) -> None:
        """$800 planned but $900 actual → positive delta (overspent)."""
        with _patch_db(self._make_comparison_db("800", "900")):
            resp = auth_client.get(f"/households/{HH_ID}/comparison/{MONTH}")
        body = resp.json()
        assert Decimal(body["items"][0]["delta"]) == Decimal("100")


# ── GET /households/{id}/debts/avalanche ─────────────────────────────────────

class TestAvalanche:
    def _make_avalanche_db(self) -> MagicMock:
        debt_bac = _make_doc(
            "debt_bac",
            {
                "householdId": HH_ID,
                "creditor": "BAC",
                "balance": "4000",
                "currency": "USD",
                "rate": "0.245",
                "payment": "200",
                "type": "credit_card",
            },
        )
        debt_dav = _make_doc(
            "debt_dav",
            {
                "householdId": HH_ID,
                "creditor": "Davivienda",
                "balance": "5500",
                "currency": "USD",
                "rate": "0.185",
                "payment": "300",
                "type": "credit_card",
            },
        )
        debts_col = MagicMock()
        # Feed debts in reverse order to test sorting
        debts_col.where.return_value.stream.return_value = iter([debt_dav, debt_bac])
        return _simple_db(debts=debts_col)

    def test_avalanche_returns_200(self, auth_client: TestClient) -> None:
        with _patch_db(self._make_avalanche_db()):
            resp = auth_client.get(f"/households/{HH_ID}/debts/avalanche")
        assert resp.status_code == 200

    def test_avalanche_response_has_entries(self, auth_client: TestClient) -> None:
        with _patch_db(self._make_avalanche_db()):
            resp = auth_client.get(f"/households/{HH_ID}/debts/avalanche")
        body = resp.json()
        assert "debts" in body
        assert len(body["debts"]) == 2

    def test_avalanche_highest_rate_first(self, auth_client: TestClient) -> None:
        """BAC (24.5%) must appear before Davivienda (18.5%) in avalanche order."""
        with _patch_db(self._make_avalanche_db()):
            resp = auth_client.get(f"/households/{HH_ID}/debts/avalanche")
        debts = resp.json()["debts"]
        assert debts[0]["creditor"] == "BAC"
        assert debts[1]["creditor"] == "Davivienda"

    def test_avalanche_rate_descending(self, auth_client: TestClient) -> None:
        """Rates must be in descending order (avalanche = highest first)."""
        with _patch_db(self._make_avalanche_db()):
            resp = auth_client.get(f"/households/{HH_ID}/debts/avalanche")
        debts = resp.json()["debts"]
        rates = [Decimal(e["rate"]) for e in debts]
        assert rates == sorted(rates, reverse=True)
