"""plan — baseline plan construction and validation.

Rules (enforced here):
- Period must have `from` < `to`.
- Every line must have amount > 0.
- Line dates must fall within the plan period (warning, not error).
- Each line currency must match its target pocket's declared currency.
- The baseline is immutable once active — it changes only via the approval flow.
- Plans can span multiple months; the pilot covers Jun–Aug 2026 (3 months).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from app.core.money import Money

# ── Build ─────────────────────────────────────────────────────────────────────

def build_plan(household_id: str, body: Any) -> tuple[dict, list[dict]]:
    """Convert a PlanCreate body into Firestore-ready dicts for plan + lines.

    Returns (plan_data, [line_data, ...]).
    Plan is created in 'draft' status; all approvals default to False.
    """
    plan_data = {
        "householdId": household_id,
        "version": 1,
        "status": "draft",
        "period": {
            "from": body.period_from.isoformat(),
            "to": body.period_to.isoformat(),
        },
        "approvals": {},
    }
    lines = [
        {
            "date": line.date.isoformat(),
            "pocketId": line.pocket_id,
            "concept": line.concept,
            "amount": str(line.amount),
            "currency": line.currency.value,
            "category": line.category,
            "type": line.type.value,
        }
        for line in body.lines
    ]
    return plan_data, lines


# ── Validate ──────────────────────────────────────────────────────────────────

def validate_plan(plan: Any) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a plan object (Plan schema or dict-like).

    Errors block activation. Warnings are advisory.

    Rules:
    - period.from must be strictly before period.to
    - every line amount must be > 0
    - line dates outside the plan period → warning
    - lines of the same concept + type + date in the same pocket → warning (possible dup)
    """
    errors: list[str] = []
    warnings: list[str] = []

    period = plan.period
    p_from = _as_date(period["from"])
    p_to = _as_date(period["to"])

    if p_from >= p_to:
        errors.append("period.from must be strictly before period.to")

    seen: dict[tuple, int] = defaultdict(int)

    for line in plan.lines:
        amount = Decimal(str(line.amount))
        if amount <= 0:
            errors.append(f"Line '{line.concept}' has non-positive amount ({amount})")

        line_date = _as_date(line.date)
        if p_from <= p_to and not (p_from <= line_date <= p_to):
            warnings.append(
                f"Line '{line.concept}' on {line_date} is outside the plan period "
                f"({p_from} → {p_to})"
            )

        # Duplicate detection
        key = (line_date, getattr(line, "pocket_id", None), line.concept, str(line.type))
        seen[key] += 1
        if seen[key] == 2:
            warnings.append(
                f"Possible duplicate: '{line.concept}' on {line_date} appears more than once"
            )

    return errors, warnings


# ── Summary helpers ───────────────────────────────────────────────────────────

def plan_income_total(plan: Any, currency: str) -> Money:
    """Sum all income lines for a given currency.

    The LLM can call this to narrate the total planned income — it doesn't compute.
    """
    total = Money(Decimal("0"), currency)
    for line in plan.lines:
        line_type = _line_type_value(line)
        line_currency = _line_currency_value(line)
        if line_type == "income" and line_currency == currency:
            total = total + Money(Decimal(str(line.amount)), currency)
    return total


def plan_expense_total(plan: Any, currency: str) -> Money:
    """Sum all expense + debt + leisure lines for a given currency."""
    total = Money(Decimal("0"), currency)
    for line in plan.lines:
        line_type = _line_type_value(line)
        line_currency = _line_currency_value(line)
        if line_type in ("expense", "debt", "leisure") and line_currency == currency:
            total = total + Money(Decimal(str(line.amount)), currency)
    return total


def lines_for_pocket(plan: Any, pocket_id: str) -> list[Any]:
    """Return all plan lines for a specific pocket (ordered by date)."""
    lines = [ln for ln in plan.lines if getattr(ln, "pocket_id", None) == pocket_id]
    return sorted(lines, key=lambda ln: _as_date(ln.date))


def lines_for_month(plan: Any, month: str) -> list[Any]:
    """Return all plan lines for a given month (YYYY-MM)."""
    return [ln for ln in plan.lines if str(_as_date(ln.date))[:7] == month]


# ── Private helpers ───────────────────────────────────────────────────────────

def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _line_type_value(line: Any) -> str:
    """Return the string value of a line's type, regardless of enum or str."""
    t = getattr(line, "type", "")
    return t.value if hasattr(t, "value") else str(t)


def _line_currency_value(line: Any) -> str:
    """Return the string value of a line's currency, regardless of enum or str."""
    c = getattr(line, "currency", "")
    return c.value if hasattr(c, "value") else str(c)
