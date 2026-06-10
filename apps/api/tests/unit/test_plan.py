"""Unit tests for app.core.plan — pure, no I/O."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.plan import (
    build_plan,
    lines_for_month,
    lines_for_pocket,
    plan_expense_total,
    plan_income_total,
    validate_plan,
)
from app.models.schemas import Currency, LineType, Plan, PlanLine, PlanStatus

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _line(
    concept: str,
    amount: str,
    line_type: LineType,
    pocket_id: str = "pocket_fau_usd",
    currency: Currency = Currency.USD,
    day: int = 14,
    month: int = 6,
) -> PlanLine:
    return PlanLine(
        id=f"line_{concept[:4].lower()}",
        date=date(2026, month, day),
        pocket_id=pocket_id,
        concept=concept,
        amount=Decimal(amount),
        currency=currency,
        category=line_type.value,
        type=line_type,
    )


def _pilot_plan(extra_lines: list[PlanLine] | None = None) -> Plan:
    """Jun–Aug 2026 pilot plan with real Fau & Mari data."""
    lines: list[PlanLine] = [
        # Incomes
        _line("Equifax quincena 1", "2018.65", LineType.income, day=14),
        _line("Equifax quincena 2", "2018.65", LineType.income, day=29),
        _line("Hyatt junio", "4295.00", LineType.income, day=15),
        _line(
            "3M salario junio", "1311667", LineType.income,
            pocket_id="pocket_mari_crc", currency=Currency.CRC, day=25,
        ),
        # Expenses
        _line("BAC atrasos", "800.00", LineType.debt, day=6),
        _line("Davivienda atrasos", "600.00", LineType.debt, day=6),
        _line("Carro junio", "380.00", LineType.debt, day=6),
        _line(
            "Escuela mayo atrasada", "120000", LineType.debt,
            pocket_id="pocket_mari_crc", currency=Currency.CRC, day=6,
        ),
        _line("Suscripciones", "43.00", LineType.expense, day=1),
    ]
    if extra_lines:
        lines.extend(extra_lines)
    return Plan(
        id="plan_jun_aug_2026_v1",
        household_id="hh_fau_mari",
        status=PlanStatus.active,
        period={"from": date(2026, 6, 1), "to": date(2026, 8, 31)},
        lines=lines,
    )


# ── Validation tests ──────────────────────────────────────────────────────────

class TestValidatePlan:
    def test_valid_plan_no_errors(self) -> None:
        plan = _pilot_plan()
        errors, warnings = validate_plan(plan)
        assert errors == []

    def test_period_from_must_be_before_to(self) -> None:
        plan = _pilot_plan()
        plan.period = {"from": date(2026, 9, 1), "to": date(2026, 8, 31)}
        errors, _ = validate_plan(plan)
        assert any("before" in e for e in errors)

    def test_period_equal_is_error(self) -> None:
        plan = _pilot_plan()
        plan.period = {"from": date(2026, 6, 1), "to": date(2026, 6, 1)}
        errors, _ = validate_plan(plan)
        assert len(errors) >= 1

    def test_non_positive_amount_is_error(self) -> None:
        bad_line = _line("Zero", "0", LineType.expense)
        plan = _pilot_plan([bad_line])
        errors, _ = validate_plan(plan)
        assert any("non-positive" in e for e in errors)

    def test_negative_amount_is_error(self) -> None:
        bad_line = _line("Negative", "-100", LineType.expense)
        plan = _pilot_plan([bad_line])
        errors, _ = validate_plan(plan)
        assert any("non-positive" in e for e in errors)

    def test_line_outside_period_is_warning(self) -> None:
        out_of_range = PlanLine(
            id="line_oor",
            date=date(2026, 5, 1),  # May — before June
            pocket_id="pocket_fau_usd",
            concept="Before period",
            amount=Decimal("100"),
            currency=Currency.USD,
            category="expense",
            type=LineType.expense,
        )
        plan = _pilot_plan([out_of_range])
        errors, warnings = validate_plan(plan)
        assert errors == []
        assert any("outside" in w for w in warnings)

    def test_duplicate_line_is_warning(self) -> None:
        dup = _line("Equifax quincena 1", "2018.65", LineType.income, day=14)
        plan = _pilot_plan([dup])
        _, warnings = validate_plan(plan)
        assert any("duplicate" in w.lower() for w in warnings)

    def test_pilot_3month_plan_is_valid(self) -> None:
        plan = _pilot_plan()
        errors, _ = validate_plan(plan)
        assert errors == []


# ── Summary helpers ───────────────────────────────────────────────────────────

class TestPlanSummaries:
    def test_income_total_usd(self) -> None:
        plan = _pilot_plan()
        total = plan_income_total(plan, "USD")
        # 2018.65 + 2018.65 + 4295.00 = 8332.30
        assert total.amount == Decimal("8332.30")
        assert total.currency == "USD"

    def test_income_total_crc(self) -> None:
        plan = _pilot_plan()
        total = plan_income_total(plan, "CRC")
        assert total.amount == Decimal("1311667")

    def test_expense_total_usd(self) -> None:
        plan = _pilot_plan()
        total = plan_expense_total(plan, "USD")
        # BAC 800 + Davivienda 600 + Carro 380 + Suscripciones 43 = 1823
        assert total.amount == Decimal("1823.00")

    def test_expense_total_crc(self) -> None:
        plan = _pilot_plan()
        total = plan_expense_total(plan, "CRC")
        assert total.amount == Decimal("120000")

    def test_lines_for_pocket(self) -> None:
        plan = _pilot_plan()
        fau_lines = lines_for_pocket(plan, "pocket_fau_usd")
        assert all(ln.pocket_id == "pocket_fau_usd" for ln in fau_lines)
        assert len(fau_lines) > 0

    def test_lines_for_pocket_ordered_by_date(self) -> None:
        plan = _pilot_plan()
        fau_lines = lines_for_pocket(plan, "pocket_fau_usd")
        dates = [ln.date for ln in fau_lines]
        assert dates == sorted(dates)

    def test_lines_for_month_june(self) -> None:
        plan = _pilot_plan()
        june = lines_for_month(plan, "2026-06")
        assert all(str(ln.date)[:7] == "2026-06" for ln in june)
        assert len(june) > 0

    def test_lines_for_month_no_results(self) -> None:
        plan = _pilot_plan()
        sep = lines_for_month(plan, "2026-09")  # after plan period
        assert sep == []


# ── build_plan ────────────────────────────────────────────────────────────────

class TestBuildPlan:
    def test_build_plan_creates_draft(self) -> None:
        from app.models.schemas import PlanCreate, PlanLineCreate

        body = PlanCreate(
            period_from=date(2026, 6, 1),
            period_to=date(2026, 8, 31),
            lines=[
                PlanLineCreate(
                    date=date(2026, 6, 14),
                    pocket_id="pocket_fau_usd",
                    concept="Equifax Q1",
                    amount=Decimal("2018.65"),
                    currency=Currency.USD,
                    category="income",
                    type=LineType.income,
                )
            ],
        )
        plan_data, line_data = build_plan("hh_fau_mari", body)
        assert plan_data["status"] == "draft"
        assert plan_data["householdId"] == "hh_fau_mari"
        assert plan_data["version"] == 1
        assert len(line_data) == 1
        assert line_data[0]["concept"] == "Equifax Q1"
        assert line_data[0]["amount"] == "2018.65"
        assert line_data[0]["currency"] == "USD"
        assert line_data[0]["type"] == "income"

    def test_build_plan_period_iso_format(self) -> None:
        from app.models.schemas import PlanCreate, PlanLineCreate

        body = PlanCreate(
            period_from=date(2026, 6, 1),
            period_to=date(2026, 8, 31),
            lines=[
                PlanLineCreate(
                    date=date(2026, 7, 1),
                    pocket_id="pocket_mari_crc",
                    concept="3M julio",
                    amount=Decimal("1311667"),
                    currency=Currency.CRC,
                    category="income",
                    type=LineType.income,
                )
            ],
        )
        plan_data, _ = build_plan("hh_fau_mari", body)
        assert plan_data["period"]["from"] == "2026-06-01"
        assert plan_data["period"]["to"] == "2026-08-31"
