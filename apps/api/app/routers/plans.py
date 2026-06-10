"""Plans router — baseline plan management.

Endpoints:
  GET  /households/{household_id}/plans        list plans (active / draft)
  POST /households/{household_id}/plans        create a draft plan
  GET  /households/{household_id}/plans/{id}   get plan + lines
  POST /households/{household_id}/plans/{id}/validate   validate plan
  POST /households/{household_id}/plans/{id}/propose    transition draft → proposed
  POST /households/{household_id}/plans/{id}/approve    cast an approval vote
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import (
    ApprovalRequest,
    Plan,
    PlanCreate,
    PlanStatus,
    PlanValidateResponse,
)
from app.security.auth import get_current_uid, require_household_member

router = APIRouter(prefix="/households/{household_id}/plans", tags=["plans"])


@router.get("", response_model=list[Plan])
def list_plans(
    household_id: str,
    uid: str = Depends(get_current_uid),
) -> list[Plan]:
    require_household_member(uid, household_id)
    from app.db.firestore import get_db

    db = get_db()
    docs = db.collection("plans").where("householdId", "==", household_id).stream()
    plans = []
    for doc in docs:
        data = doc.to_dict()
        lines_ref = doc.reference.collection("lines").stream()
        lines_data = [{"id": ln.id, **ln.to_dict()} for ln in lines_ref]
        plans.append(_doc_to_plan(doc.id, data, lines_data))
    return plans


@router.post("", response_model=Plan, status_code=status.HTTP_201_CREATED)
def create_plan(
    household_id: str,
    body: PlanCreate,
    uid: str = Depends(get_current_uid),
) -> Plan:
    require_household_member(uid, household_id)
    from app.core.plan import build_plan
    from app.db.firestore import get_db

    db = get_db()
    plan_data, line_data_list = build_plan(household_id, body)
    plan_ref = db.collection("plans").document()
    plan_ref.set(plan_data)
    for line in line_data_list:
        plan_ref.collection("lines").document().set(line)

    # Return freshly created plan
    plan_doc = plan_ref.get()
    lines = [{"id": ln.id, **ln.to_dict()} for ln in plan_ref.collection("lines").stream()]
    return _doc_to_plan(plan_ref.id, plan_doc.to_dict(), lines)


@router.get("/{plan_id}", response_model=Plan)
def get_plan(
    household_id: str,
    plan_id: str,
    uid: str = Depends(get_current_uid),
) -> Plan:
    require_household_member(uid, household_id)
    return _fetch_plan(household_id, plan_id)


@router.post("/{plan_id}/validate", response_model=PlanValidateResponse)
def validate_plan(
    household_id: str,
    plan_id: str,
    uid: str = Depends(get_current_uid),
) -> PlanValidateResponse:
    require_household_member(uid, household_id)
    from app.core.plan import validate_plan as core_validate

    plan = _fetch_plan(household_id, plan_id)
    errors, warnings = core_validate(plan)
    return PlanValidateResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)


@router.post("/{plan_id}/propose", response_model=Plan)
def propose_plan(
    household_id: str,
    plan_id: str,
    uid: str = Depends(get_current_uid),
) -> Plan:
    require_household_member(uid, household_id)
    from app.db.firestore import get_db

    db = get_db()
    ref = db.collection("plans").document(plan_id)
    doc = ref.get()
    if not doc.exists or doc.to_dict().get("householdId") != household_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    ref.update({"status": PlanStatus.proposed.value})
    return _fetch_plan(household_id, plan_id)


@router.post("/{plan_id}/approve", response_model=Plan)
def approve_plan(
    household_id: str,
    plan_id: str,
    body: ApprovalRequest,
    uid: str = Depends(get_current_uid),
) -> Plan:
    require_household_member(uid, household_id)
    from app.db.firestore import get_db

    db = get_db()
    ref = db.collection("plans").document(plan_id)
    doc = ref.get()
    if not doc.exists or doc.to_dict().get("householdId") != household_id:
        raise HTTPException(status_code=404, detail="Plan not found")

    approvals = doc.to_dict().get("approvals", {})
    approvals[body.uid] = body.approved
    update: dict = {"approvals": approvals}

    # Fetch household members to check if all approved
    hh_doc = db.collection("households").document(household_id).get()
    members: list[str] = hh_doc.to_dict().get("members", [])
    if all(approvals.get(m) for m in members):
        update["status"] = PlanStatus.active.value
        # Archive previous active plan
        prev = (
            db.collection("plans")
            .where("householdId", "==", household_id)
            .where("status", "==", PlanStatus.active.value)
            .stream()
        )
        for p in prev:
            if p.id != plan_id:
                p.reference.update({"status": PlanStatus.archived.value})

    ref.update(update)
    return _fetch_plan(household_id, plan_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_plan(household_id: str, plan_id: str) -> Plan:
    from app.db.firestore import get_db

    db = get_db()
    ref = db.collection("plans").document(plan_id)
    doc = ref.get()
    if not doc.exists or doc.to_dict().get("householdId") != household_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    lines = [{"id": ln.id, **ln.to_dict()} for ln in ref.collection("lines").stream()]
    return _doc_to_plan(plan_id, doc.to_dict(), lines)


def _doc_to_plan(plan_id: str, data: dict, lines_raw: list[dict]) -> Plan:
    from app.models.schemas import PlanLine

    lines = []
    for ln in lines_raw:
        lines.append(
            PlanLine(
                id=ln["id"],
                date=ln["date"],
                pocket_id=ln["pocketId"],
                concept=ln["concept"],
                amount=ln["amount"],
                currency=ln["currency"],
                category=ln.get("category", "general"),
                type=ln["type"],
            )
        )
    return Plan(
        id=plan_id,
        household_id=data["householdId"],
        version=data.get("version", 1),
        status=data["status"],
        period={"from": data["period"]["from"], "to": data["period"]["to"]},
        approvals=data.get("approvals", {}),
        lines=lines,
    )
