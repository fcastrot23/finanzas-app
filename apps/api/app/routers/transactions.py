"""Transactions router — ledger (real spend/income against the plan)."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import Transaction, TransactionCreate, TransactionUpdate, TxStatus
from app.security.auth import get_current_uid, require_household_member

router = APIRouter(prefix="/households/{household_id}/transactions", tags=["transactions"])


@router.get("", response_model=list[Transaction])
def list_transactions(
    household_id: str,
    month: str | None = None,
    pocket_id: str | None = None,
    uid: str = Depends(get_current_uid),
) -> list[Transaction]:
    """List transactions for the household. Filter by month (YYYY-MM) or pocket."""
    require_household_member(uid, household_id)
    from app.db.firestore import get_db

    db = get_db()
    q = db.collection("transactions").where("householdId", "==", household_id)
    if pocket_id:
        q = q.where("pocketId", "==", pocket_id)
    txs = []
    for doc in q.stream():
        txs.append(_doc_to_tx(doc.id, doc.to_dict()))

    if month:
        txs = [t for t in txs if str(t.date)[:7] == month]
    return sorted(txs, key=lambda t: t.date)


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    household_id: str,
    body: TransactionCreate,
    uid: str = Depends(get_current_uid),
) -> Transaction:
    require_household_member(uid, household_id)
    from app.db.firestore import get_db

    db = get_db()
    data = {
        "householdId": household_id,
        "pocketId": body.pocket_id,
        "date": body.date.isoformat(),
        "concept": body.concept,
        "amount": str(body.amount),
        "currency": body.currency.value,
        "fx": str(body.fx) if body.fx is not None else None,
        "planLineId": body.plan_line_id,
        "status": TxStatus.in_plan.value if body.plan_line_id else TxStatus.out_of_plan.value,
        "category": body.category,
        "split": [{"uid": s.uid, "amount": str(s.amount)} for s in body.split],
        "createdAt": datetime.now(UTC).isoformat(),
    }
    ref = db.collection("transactions").document()
    ref.set(data)
    return _doc_to_tx(ref.id, data)


@router.get("/{tx_id}", response_model=Transaction)
def get_transaction(
    household_id: str,
    tx_id: str,
    uid: str = Depends(get_current_uid),
) -> Transaction:
    require_household_member(uid, household_id)
    return _fetch_tx(household_id, tx_id)


@router.patch("/{tx_id}", response_model=Transaction)
def update_transaction(
    household_id: str,
    tx_id: str,
    body: TransactionUpdate,
    uid: str = Depends(get_current_uid),
) -> Transaction:
    require_household_member(uid, household_id)
    from app.db.firestore import get_db

    db = get_db()
    ref = db.collection("transactions").document(tx_id)
    doc = ref.get()
    if not doc.exists or doc.to_dict().get("householdId") != household_id:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update: dict = {}
    if body.plan_line_id is not None:
        update["planLineId"] = body.plan_line_id
        update["status"] = TxStatus.in_plan.value
    if body.category is not None:
        update["category"] = body.category
    if body.split is not None:
        update["split"] = [{"uid": s.uid, "amount": str(s.amount)} for s in body.split]

    if update:
        ref.update(update)
    return _fetch_tx(household_id, tx_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_tx(household_id: str, tx_id: str) -> Transaction:
    from app.db.firestore import get_db

    db = get_db()
    doc = db.collection("transactions").document(tx_id).get()
    if not doc.exists or doc.to_dict().get("householdId") != household_id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _doc_to_tx(tx_id, doc.to_dict())


def _doc_to_tx(tx_id: str, data: dict) -> Transaction:
    from datetime import date

    from app.models.schemas import TxSplit

    split = [TxSplit(uid=s["uid"], amount=s["amount"]) for s in data.get("split", [])]
    return Transaction(
        id=tx_id,
        household_id=data["householdId"],
        pocket_id=data["pocketId"],
        date=date.fromisoformat(str(data["date"])[:10]),
        concept=data["concept"],
        amount=data["amount"],
        currency=data["currency"],
        fx=data.get("fx"),
        plan_line_id=data.get("planLineId"),
        status=data["status"],
        category=data.get("category", "general"),
        split=split,
        created_at=data.get("createdAt"),
    )
