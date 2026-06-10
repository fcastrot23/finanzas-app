"""matching — transaction → plan line suggestion and partial payment support.

Rules:
- The engine produces *suggestions* with a confidence score (0.0–1.0).
- The user confirms or overrides; the engine never auto-commits.
- A plan line can be partially paid by multiple transactions (abonos).
- "Out of plan" transactions are legitimate — they don't fail, they're tracked separately.
- Matching is based on: concept similarity, amount proximity, date proximity.
- The LLM narrates the suggestion; this module computes it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class MatchSuggestion:
    """A suggested match between a transaction and a plan line."""

    plan_line_id: str
    plan_line_concept: str
    confidence: float  # 0.0–1.0
    reason: str
    amount_matched: Decimal  # amount of the transaction being applied
    amount_remaining_on_line: Decimal  # how much of the plan line is still open


@dataclass
class PartialPaymentStatus:
    """Aggregated payment status for a single plan line."""

    plan_line_id: str
    planned_amount: Decimal
    paid_amount: Decimal
    remaining: Decimal
    is_fully_paid: bool
    payment_count: int


def suggest_line(
    transaction: Any,
    plan_lines: list[Any],
    paid_amounts: dict[str, Decimal] | None = None,
) -> MatchSuggestion | None:
    """Suggest the best matching plan line for a transaction.

    Scoring weights:
    - Concept similarity: 0.50
    - Amount proximity:   0.30
    - Date proximity:     0.20

    Returns the best suggestion above MIN_CONFIDENCE (0.25), or None.

    paid_amounts: dict of plan_line_id -> already-paid Decimal (for partial tracking).
    """
    MIN_CONFIDENCE = 0.25

    if not plan_lines:
        return None

    paid = paid_amounts or {}
    tx_concept: str = getattr(transaction, "concept", "") or ""
    tx_amount: Decimal = Decimal(str(getattr(transaction, "amount", 0)))
    tx_date_raw = getattr(transaction, "date", None)
    tx_date: date | None = _as_date(tx_date_raw) if tx_date_raw else None
    tx_currency_raw = getattr(transaction, "currency", "")
    tx_currency: str = (
        tx_currency_raw.value if hasattr(tx_currency_raw, "value") else str(tx_currency_raw).upper()
    )

    best: MatchSuggestion | None = None
    best_score: float = 0.0

    for line in plan_lines:
        line_id: str = getattr(line, "id", "") or ""
        line_concept: str = getattr(line, "concept", "") or ""
        line_amount: Decimal = Decimal(str(getattr(line, "amount", 0)))
        line_currency_raw = getattr(line, "currency", "")
        line_currency: str = (
            line_currency_raw.value
            if hasattr(line_currency_raw, "value")
            else str(line_currency_raw).upper()
        )
        line_date_raw = getattr(line, "date", None)
        line_date: date | None = _as_date(line_date_raw) if line_date_raw else None

        # Skip lines with a different currency — pockets never mix
        if line_currency and tx_currency and line_currency != tx_currency:
            continue

        # Concept score (0.0–0.5)
        concept_score = _concept_similarity(tx_concept, line_concept) * 0.5

        # Amount score (0.0–0.3)
        already_paid = paid.get(line_id, Decimal("0"))
        remaining_on_line = max(Decimal("0"), line_amount - already_paid)
        amount_score = _amount_proximity(tx_amount, remaining_on_line) * 0.3

        # Date score (0.0–0.2)
        date_score = (
            _date_proximity(tx_date, line_date) if tx_date and line_date else 0.0
        ) * 0.2

        score = concept_score + amount_score + date_score

        if score > best_score and score >= MIN_CONFIDENCE:
            best_score = score
            best = MatchSuggestion(
                plan_line_id=line_id,
                plan_line_concept=line_concept,
                confidence=round(score, 4),
                reason=_build_reason(concept_score, amount_score, date_score),
                amount_matched=tx_amount,
                amount_remaining_on_line=remaining_on_line,
            )

    return best


def partial_payment_status(
    plan_line_id: str,
    planned_amount: Decimal,
    transactions: list[Any],
) -> PartialPaymentStatus:
    """Compute how much of a plan line has been paid by the given transactions.

    Supports abonos de buena fe — multiple transactions toward the same line.
    """
    paid = Decimal("0")
    count = 0
    for tx in transactions:
        if isinstance(tx, dict):
            line_id = tx.get("planLineId")
            amount = Decimal(str(tx.get("amount", 0)))
        else:
            line_id = getattr(tx, "plan_line_id", None)
            amount = Decimal(str(getattr(tx, "amount", 0)))
        if line_id == plan_line_id:
            paid += amount
            count += 1

    remaining = max(Decimal("0"), planned_amount - paid)
    return PartialPaymentStatus(
        plan_line_id=plan_line_id,
        planned_amount=planned_amount,
        paid_amount=paid,
        remaining=remaining,
        is_fully_paid=paid >= planned_amount,
        payment_count=count,
    )


def unmatched_transactions(transactions: list[Any]) -> list[Any]:
    """Return transactions not yet matched to any plan line (out_of_plan)."""
    result = []
    for tx in transactions:
        if isinstance(tx, dict):
            status = tx.get("status", "")
            plan_line = tx.get("planLineId")
        else:
            status = str(getattr(tx, "status", ""))
            plan_line = getattr(tx, "plan_line_id", None)
        if status == "out_of_plan" or not plan_line:
            result.append(tx)
    return result


# Scoring helpers

def _concept_similarity(a: str, b: str) -> float:
    """Token-overlap (Jaccard) similarity. Returns 0.0–1.0."""
    if not a or not b:
        return 0.0
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())
    if not a_tokens or not b_tokens:
        return 0.0
    if a.lower().strip() == b.lower().strip():
        return 1.0
    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    jaccard = len(intersection) / len(union)
    return min(1.0, jaccard * 1.5)  # slight boost for partial overlap


def _amount_proximity(tx_amount: Decimal, line_amount: Decimal) -> float:
    """Ratio of smaller to larger amount. Returns 0.0–1.0."""
    if line_amount == 0 or tx_amount == 0:
        return 0.0
    return float(min(tx_amount, line_amount) / max(tx_amount, line_amount))


def _date_proximity(tx_date: date, line_date: date) -> float:
    """Proximity score based on days apart. Full score within 3 days."""
    delta = abs((tx_date - line_date).days)
    if delta == 0:
        return 1.0
    if delta <= 3:
        return 0.8
    if delta <= 7:
        return 0.5
    if delta <= 14:
        return 0.2
    return 0.0


def _build_reason(concept_score: float, amount_score: float, date_score: float) -> str:
    parts = []
    if concept_score >= 0.3:
        parts.append("concepto similar")
    if amount_score >= 0.2:
        parts.append("monto cercano")
    if date_score >= 0.1:
        parts.append("fecha próxima")
    return ", ".join(parts) if parts else "coincidencia parcial"


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])
