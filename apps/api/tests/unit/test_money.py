"""Unit tests for app.core.money — pure, no I/O."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.core.money import Money, convert, fx_for_date, sum_money


class TestMoney:
    def test_add_same_currency(self) -> None:
        a = Money("1000", "CRC")
        b = Money("500", "CRC")
        assert (a + b).amount == Decimal("1500")
        assert (a + b).currency == "CRC"

    def test_add_different_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot add"):
            Money("100", "USD") + Money("200", "CRC")

    def test_sub_same_currency(self) -> None:
        a = Money("1000", "USD")
        b = Money("300", "USD")
        result = a - b
        assert result.amount == Decimal("700")

    def test_sub_different_currency_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot subtract"):
            Money("100", "CRC") - Money("10", "USD")

    def test_to_usd_from_crc(self) -> None:
        # Pilot case: ₡470,000 / 470 = $1,000
        m = Money("470000", "CRC")
        usd = m.to_usd(Decimal("470"))
        assert usd.currency == "USD"
        assert usd.amount == Decimal("1000.00")

    def test_to_crc_from_usd(self) -> None:
        # $2,018.65 × 470 = ₡948,765.50 → rounds to ₡948,766 (CRC has no cents)
        m = Money("2018.65", "USD")
        crc = m.to_crc(Decimal("470"))
        assert crc.currency == "CRC"
        assert crc.amount == Decimal("948766")  # ROUND_HALF_UP: .50 → 1

    def test_to_usd_already_usd(self) -> None:
        m = Money("100", "USD")
        assert m.to_usd(Decimal("470")) == m

    def test_to_crc_already_crc(self) -> None:
        m = Money("50000", "CRC")
        assert m.to_crc(Decimal("470")) == m

    def test_equality(self) -> None:
        assert Money("100", "USD") == Money("100", "USD")
        assert Money("100", "USD") != Money("100", "CRC")

    def test_repr(self) -> None:
        assert "CRC" in repr(Money("1000", "CRC"))
        assert "USD" in repr(Money("100", "USD"))


class TestConvert:
    def test_convert_crc_to_usd(self) -> None:
        result = convert(Decimal("470000"), "CRC", "USD", Decimal("470"))
        assert result == Decimal("1000.00")

    def test_convert_usd_to_crc(self) -> None:
        result = convert(Decimal("1000"), "USD", "CRC", Decimal("470"))
        assert result == Decimal("470000")

    def test_convert_same_currency(self) -> None:
        result = convert(Decimal("500"), "USD", "USD", None)
        assert result == Decimal("500")

    def test_convert_requires_fx_rate(self) -> None:
        with pytest.raises(ValueError, match="FX rate required"):
            convert(Decimal("1000"), "CRC", "USD", None)

    def test_pilot_case_fau_biweekly_to_crc(self) -> None:
        # Equifax $2,018.65 × ₡470/USD = ₡948,765.50 → ₡948,766 (integer CRC)
        result = convert(Decimal("2018.65"), "USD", "CRC", Decimal("470"))
        assert result == Decimal("948766")

    def test_pilot_case_mari_salary_monthly(self) -> None:
        # Mari 3M ₡1,311,667 / ₡470 = $2,790.78 (≈$2,791 rounded in docs)
        result = convert(Decimal("1311667"), "CRC", "USD", Decimal("470"))
        assert result == Decimal("2790.78")


class TestMoneyExtended:
    def test_format_crc_no_cents(self) -> None:
        m = Money("1311667", "CRC")
        assert m.format() == "₡1,311,667 CRC"

    def test_format_usd_with_cents(self) -> None:
        m = Money("2018.65", "USD")
        assert m.format() == "$2,018.65 USD"

    def test_format_no_currency_label(self) -> None:
        m = Money("500", "USD")
        assert m.format(show_currency=False) == "$500.00"

    def test_neg(self) -> None:
        m = Money("100", "USD")
        assert (-m).amount == Decimal("-100")

    def test_abs_positive(self) -> None:
        m = Money("100", "CRC")
        assert abs(m) == m

    def test_abs_negative(self) -> None:
        m = Money("-50000", "CRC")
        assert abs(m).amount == Decimal("50000")

    def test_comparison_lt(self) -> None:
        assert Money("100", "USD") < Money("200", "USD")

    def test_comparison_cross_currency_raises(self) -> None:
        with pytest.raises(ValueError):
            _ = Money("100", "USD") < Money("200", "CRC")

    def test_is_zero(self) -> None:
        assert Money("0", "CRC").is_zero()
        assert not Money("1", "CRC").is_zero()

    def test_is_positive(self) -> None:
        assert Money("100", "USD").is_positive()
        assert not Money("-1", "USD").is_positive()

    def test_is_negative(self) -> None:
        assert Money("-1", "CRC").is_negative()
        assert not Money("0", "CRC").is_negative()

    def test_convert_to_usd(self) -> None:
        m = Money("470000", "CRC")
        assert m.convert_to("USD", Decimal("470")) == Money("1000.00", "USD")

    def test_convert_to_crc(self) -> None:
        m = Money("1000", "USD")
        assert m.convert_to("CRC", Decimal("470")) == Money("470000", "CRC")


class TestSumMoney:
    def test_sum_usd(self) -> None:
        items = [Money("100", "USD"), Money("200", "USD"), Money("50.50", "USD")]
        result = sum_money(items, "USD")
        assert result.amount == Decimal("350.50")
        assert result.currency == "USD"

    def test_sum_crc(self) -> None:
        items = [Money("500000", "CRC"), Money("811667", "CRC")]
        result = sum_money(items, "CRC")
        assert result.amount == Decimal("1311667")

    def test_sum_empty(self) -> None:
        result = sum_money([], "USD")
        assert result.is_zero()

    def test_sum_cross_currency_raises(self) -> None:
        with pytest.raises(ValueError):
            sum_money([Money("100", "USD"), Money("100", "CRC")], "USD")

    def test_pilot_total_fau_monthly_income(self) -> None:
        # Equifax $2,018.65 × 2 quincenal = $4,037/month + Hyatt $4,295
        equifax_1 = Money("2018.65", "USD")
        equifax_2 = Money("2018.65", "USD")
        hyatt = Money("4295", "USD")
        total = sum_money([equifax_1, equifax_2, hyatt], "USD")
        assert total.amount == Decimal("8332.30")


class TestFxForDate:
    def test_returns_pilot_default(self) -> None:
        rate = fx_for_date(date(2026, 6, 1))
        assert rate == Decimal("470")

    def test_respects_household_ref(self) -> None:
        rate = fx_for_date(date(2026, 6, 1), household_fx_ref=Decimal("475"))
        assert rate == Decimal("475")

    def test_none_ref_uses_default(self) -> None:
        rate = fx_for_date(date(2026, 7, 15), household_fx_ref=None)
        assert rate == Decimal("470")
