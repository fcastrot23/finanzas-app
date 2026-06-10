"""Unit tests for app.core.matching — pure, no I/O."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest

from app.core.matching import (
    _amount_proximity,
    _concept_similarity,
    _date_proximity,
    partial_payment_status,
    suggest_line,
    unmatched_transactions,
)

# ── Stub objects (no Pydantic overhead) ───────────────────────────────────────

@dataclass
class FakeTx:
    concept: str
    amount: str
    currency: str = "USD"
    date: date | None = None
    plan_line_id: str | None = None
    status: str = "out_of_plan"


@dataclass
class FakeLine:
    id: str
    concept: str
    amount: str
    currency: str = "USD"
    date: date | None = None


# ── Scoring unit tests ────────────────────────────────────────────────────────

class TestConceptSimilarity:
    def test_exact_match(self) -> None:
        assert _concept_similarity("BAC tarjeta", "BAC tarjeta") == 1.0

    def test_partial_overlap(self) -> None:
        score = _concept_similarity("BAC tarjeta Fau", "BAC atrasos")
        assert 0.0 < score < 1.0

    def test_no_overlap(self) -> None:
        assert _concept_similarity("Escuela", "BAC tarjeta") == 0.0

    def test_empty_strings(self) -> None:
        assert _concept_similarity("", "BAC") == 0.0
        assert _concept_similarity("BAC", "") == 0.0


class TestAmountProximity:
    def test_exact_match(self) -> None:
        assert _amount_proximity(Decimal("400"), Decimal("400")) == 1.0

    def test_half_paid(self) -> None:
        # Transaction is half the line amount
        score = _amount_proximity(Decimal("200"), Decimal("400"))
        assert score == pytest.approx(0.5)

    def test_zero_line_amount(self) -> None:
        assert _amount_proximity(Decimal("100"), Decimal("0")) == 0.0

    def test_zero_tx_amount(self) -> None:
        assert _amount_proximity(Decimal("0"), Decimal("100")) == 0.0


class TestDateProximity:
    def test_same_day(self) -> None:
        assert _date_proximity(date(2026, 6, 6), date(2026, 6, 6)) == 1.0

    def test_2_days_apart(self) -> None:
        assert _date_proximity(date(2026, 6, 4), date(2026, 6, 6)) == 0.8

    def test_5_days_apart(self) -> None:
        assert _date_proximity(date(2026, 6, 1), date(2026, 6, 6)) == 0.5

    def test_10_days_apart(self) -> None:
        assert _date_proximity(date(2026, 6, 1), date(2026, 6, 11)) == 0.2

    def test_30_days_apart(self) -> None:
        assert _date_proximity(date(2026, 6, 1), date(2026, 7, 1)) == 0.0


# ── suggest_line ──────────────────────────────────────────────────────────────

class TestSuggestLine:
    def test_exact_concept_match_high_confidence(self) -> None:
        tx = FakeTx("BAC tarjeta", "400", date=date(2026, 6, 6))
        line = FakeLine("l1", "BAC tarjeta", "400", date=date(2026, 6, 6))
        result = suggest_line(tx, [line])
        assert result is not None
        assert result.plan_line_id == "l1"
        assert result.confidence > 0.8

    def test_no_match_returns_none(self) -> None:
        tx = FakeTx("Supermercado Walmart", "500", date=date(2026, 6, 1))
        line = FakeLine("l1", "BAC tarjeta", "400")
        result = suggest_line(tx, [line])
        assert result is None

    def test_empty_lines_returns_none(self) -> None:
        tx = FakeTx("BAC", "400")
        assert suggest_line(tx, []) is None

    def test_currency_mismatch_skipped(self) -> None:
        tx = FakeTx("Escuela", "120000", currency="CRC")
        line = FakeLine("l1", "Escuela", "120000", currency="USD")  # wrong currency
        result = suggest_line(tx, [line])
        assert result is None

    def test_currency_match_included(self) -> None:
        tx = FakeTx("Escuela", "120000", currency="CRC", date=date(2026, 6, 6))
        line = FakeLine("l1", "Escuela", "120000", currency="CRC", date=date(2026, 6, 6))
        result = suggest_line(tx, [line])
        assert result is not None

    def test_pilot_case_bac_payment(self) -> None:
        """Pilot: BAC payment on Jun 6 matches plan line."""
        tx = FakeTx("BAC tarjeta — abono", "800", date=date(2026, 6, 6))
        lines = [
            FakeLine("l_bac", "BAC tarjeta — atrasos May+Jun", "800", date=date(2026, 6, 6)),
            FakeLine("l_car", "Carro — cuota junio", "380", date=date(2026, 6, 6)),
        ]
        result = suggest_line(tx, lines)
        assert result is not None
        assert result.plan_line_id == "l_bac"

    def test_pilot_case_escuela_partial(self) -> None:
        """Pilot: Escuela abono partial (₡100k on ₡120k line)."""
        tx = FakeTx("Escuela pago parcial", "100000", currency="CRC", date=date(2026, 6, 7))
        lines = [
            FakeLine("l_esc", "Escuela mensualidad mayo", "120000", currency="CRC", date=date(2026, 6, 6)),
        ]
        result = suggest_line(tx, lines)
        assert result is not None
        assert result.plan_line_id == "l_esc"
        assert result.amount_remaining_on_line == Decimal("120000")  # no prior payments

    def test_partial_payment_reduces_remaining(self) -> None:
        """When ₡60k already paid on ₡120k line, remaining shows ₡60k."""
        tx = FakeTx("Escuela cuota", "60000", currency="CRC")
        lines = [FakeLine("l_esc", "Escuela cuota", "120000", currency="CRC")]
        paid = {"l_esc": Decimal("60000")}
        result = suggest_line(tx, lines, paid_amounts=paid)
        assert result is not None
        assert result.amount_remaining_on_line == Decimal("60000")

    def test_picks_best_among_multiple_candidates(self) -> None:
        tx = FakeTx("Davivienda cuota", "300", date=date(2026, 6, 6))
        lines = [
            FakeLine("l_bac", "BAC tarjeta cuota", "400", date=date(2026, 6, 6)),
            FakeLine("l_dav", "Davivienda cuota mensual", "300", date=date(2026, 6, 6)),
        ]
        result = suggest_line(tx, lines)
        assert result is not None
        assert result.plan_line_id == "l_dav"


# ── partial_payment_status ────────────────────────────────────────────────────

class TestPartialPaymentStatus:
    def test_no_payments(self) -> None:
        status = partial_payment_status("l1", Decimal("120000"), [])
        assert status.paid_amount == Decimal("0")
        assert status.remaining == Decimal("120000")
        assert status.is_fully_paid is False
        assert status.payment_count == 0

    def test_single_full_payment(self) -> None:
        txs = [{"planLineId": "l1", "amount": "120000"}]
        status = partial_payment_status("l1", Decimal("120000"), txs)
        assert status.is_fully_paid is True
        assert status.remaining == Decimal("0")
        assert status.payment_count == 1

    def test_pilot_abonos_de_buena_fe(self) -> None:
        """Pilot: Escuela ₡120k paid in two installments of ₡60k each."""
        txs = [
            {"planLineId": "l_esc", "amount": "60000"},
            {"planLineId": "l_esc", "amount": "60000"},
            {"planLineId": "l_other", "amount": "999"},  # different line, should be ignored
        ]
        status = partial_payment_status("l_esc", Decimal("120000"), txs)
        assert status.paid_amount == Decimal("120000")
        assert status.is_fully_paid is True
        assert status.payment_count == 2

    def test_partial_payment(self) -> None:
        txs = [{"planLineId": "l1", "amount": "800"}]
        status = partial_payment_status("l1", Decimal("1200"), txs)
        assert status.paid_amount == Decimal("800")
        assert status.remaining == Decimal("400")
        assert status.is_fully_paid is False


# ── unmatched_transactions ────────────────────────────────────────────────────

class TestUnmatchedTransactions:
    def test_all_unmatched(self) -> None:
        txs = [
            {"status": "out_of_plan", "planLineId": None},
            {"status": "out_of_plan", "planLineId": None},
        ]
        result = unmatched_transactions(txs)
        assert len(result) == 2

    def test_matched_excluded(self) -> None:
        txs = [
            {"status": "in_plan", "planLineId": "l1"},
            {"status": "out_of_plan", "planLineId": None},
        ]
        result = unmatched_transactions(txs)
        assert len(result) == 1

    def test_pilot_moose_is_unmatched(self) -> None:
        """Moose (ocio hogar) was not in the plan — it's out_of_plan."""
        moose = {"concept": "Moose — salida familiar", "status": "out_of_plan", "planLineId": None}
        result = unmatched_transactions([moose])
        assert len(result) == 1
        assert result[0]["concept"] == "Moose — salida familiar"
