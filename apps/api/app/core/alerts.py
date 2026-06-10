"""alerts — proactive overspend and budget alerts.

Rules:
- Alerts are generated from plan vs. actual comparison data (no LLM involvement).
- Severity levels: red = overspent, amber = near cap (>80%), info = general.
- The LLM never decides what constitutes an alert; this module does.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

NEAR_CAP_THRESHOLD = Decimal("0.80")


def generate_alerts(db: Any, household_id: str, month: str | None = None) -> list[Any]:
    """Generate proactive alerts for the household for the given month.

    Checks:
    - Overspend per pocket: actual > planned → red alert
    - Near-cap per pocket: actual > 80% of planned → amber alert
    - Unmatched transactions: out-of-plan spending → info alert

    Returns a list of Alert objects (empty if no issues found).
    """
    from app.core.comparison import compare_plan_actual
    from app.models.schemas import Alert, AlertSeverity

    if month is None:
        month = date.today().strftime("%Y-%m")

    comparison = compare_plan_actual(db, household_id, month)
    alerts: list[Alert] = []

    for item in comparison.items:
        planned = item.planned
        actual = item.actual
        delta = item.delta  # actual - planned (positive = overspent)
        pocket_name = item.pocket_name or item.pocket_id

        if delta > Decimal("0"):
            alerts.append(Alert(
                alert_id=f"overspend_{item.pocket_id}_{month}",
                household_id=household_id,
                type="overspend",
                severity=AlertSeverity.red,
                message=(
                    f'Bolsillo “{pocket_name}”: gastaste {actual} vs '
                    f"{planned} planificado (+{delta})."
                ),
                pocket_id=item.pocket_id,
                month=month,
            ))
        elif planned > Decimal("0") and delta < Decimal("0") and actual / planned > NEAR_CAP_THRESHOLD:
            pct_used = int((actual / planned * 100).quantize(Decimal("1")))
            alerts.append(Alert(
                alert_id=f"near_cap_{item.pocket_id}_{month}",
                household_id=household_id,
                type="near_cap",
                severity=AlertSeverity.amber,
                message=(
                    f'Bolsillo "{pocket_name}": {pct_used}% del presupuesto usado '
                    f"({actual} de {planned})."
                ),
                pocket_id=item.pocket_id,
                month=month,
            ))

    # Unmatched transactions alert (transactions with out_of_plan status)
    unmatched = _count_unmatched(db, household_id, month)
    if unmatched > 0:
        alerts.append(Alert(
            alert_id=f"unmatched_{household_id}_{month}",
            household_id=household_id,
            type="unmatched_tx",
            severity=AlertSeverity.info,
            message=f"Hay {unmatched} transacción(es) sin plan asignado este mes.",
            pocket_id=None,
            month=month,
        ))

    return alerts


def _count_unmatched(db: Any, household_id: str, month: str) -> int:
    """Count transactions with status='out_of_plan' for this household and month."""
    txs = db.collection("transactions").where("householdId", "==", household_id).stream()
    count = 0
    for td in txs:
        tx = td.to_dict()
        if str(tx.get("date", ""))[:7] != month:
            continue
        if tx.get("status") == "out_of_plan":
            count += 1
    return count


def close_month(db: Any, household_id: str, month: str | None = None) -> Any:
    """Archive the active plan, generate a monthly report, and return alerts.

    Steps:
    1. Archive the currently active plan (status → archived).
    2. Run comparison for the closing month.
    3. Generate alerts for the month.
    4. Return CloseMonthResponse.
    """
    from app.core.comparison import compare_plan_actual
    from app.models.schemas import CloseMonthResponse

    if month is None:
        month = date.today().strftime("%Y-%m")

    # 1. Archive active plan
    archived_plan_id: str | None = None
    plans_stream = (
        db.collection("plans")
        .where("householdId", "==", household_id)
        .where("status", "==", "active")
        .stream()
    )
    for plan_doc in plans_stream:
        plan_doc.reference.update({"status": "archived"})
        archived_plan_id = plan_doc.id
        break  # at most one active plan

    # 2. Comparison report
    comparison = compare_plan_actual(db, household_id, month)

    # 3. Alerts
    alerts = generate_alerts(db, household_id, month)

    return CloseMonthResponse(
        household_id=household_id,
        month=month,
        archived_plan_id=archived_plan_id,
        alert_count=len(alerts),
        alerts=alerts,
        total_planned=comparison.total_planned,
        total_actual=comparison.total_actual,
        total_delta=comparison.total_delta,
    )
