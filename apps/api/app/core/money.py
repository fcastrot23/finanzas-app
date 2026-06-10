"""money — Money value object, FX conversion, and formatting.

Rules (enforced here, never bypassed by the LLM):
- Currency is always explicit — no implicit conversions.
- CRC ↔ USD conversions require an explicit FX rate (stored per transaction).
- All arithmetic returns a new Money; amounts never become floats.
- The pilot reference rate is ₡470/USD (Jun 2026); stored per-transaction for accuracy.
"""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class Money:
    """Immutable money value — amount + currency.

    Core never mixes currencies implicitly. Every cross-currency operation
    requires an explicit FX rate; no silent coercion happens.
    """

    __slots__ = ("amount", "currency")

    def __init__(self, amount: Decimal | str | int, currency: str) -> None:
        self.amount = Decimal(str(amount))
        self.currency = currency.upper()

    # ── Arithmetic (same-currency only) ───────────────────────────────────────

    def __add__(self, other: Money) -> Money:
        _require_same_currency(self, other, "add")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        _require_same_currency(self, other, "subtract")
        return Money(self.amount - other.amount, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __abs__(self) -> Money:
        return Money(abs(self.amount), self.currency)

    # ── Comparison ────────────────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: Money) -> bool:
        _require_same_currency(self, other, "compare")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        _require_same_currency(self, other, "compare")
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        return not self.__le__(other)

    def __ge__(self, other: Money) -> bool:
        return not self.__lt__(other)

    # ── Formatting ────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return self.format()

    def format(self, *, show_currency: bool = True) -> str:
        """Human-readable: ₡1,311,667 CRC or $2,018.65 USD."""
        if self.currency == "CRC":
            # CRC: no cents (integers), thousands separator
            formatted = f"₡{self.amount:,.0f}"
        else:
            formatted = f"${self.amount:,.2f}"
        return f"{formatted} {self.currency}" if show_currency else formatted

    # ── FX conversion ─────────────────────────────────────────────────────────

    def to_usd(self, fx_rate: Decimal) -> Money:
        """Convert CRC → USD. fx_rate = ₡ per 1 USD (e.g. Decimal('470'))."""
        if self.currency == "USD":
            return Money(self.amount, "USD")
        if self.currency != "CRC":
            raise ValueError(f"No CRC→USD conversion for currency '{self.currency}'")
        converted = (self.amount / fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Money(converted, "USD")

    def to_crc(self, fx_rate: Decimal) -> Money:
        """Convert USD → CRC. fx_rate = ₡ per 1 USD (e.g. Decimal('470'))."""
        if self.currency == "CRC":
            return Money(self.amount, "CRC")
        if self.currency != "USD":
            raise ValueError(f"No USD→CRC conversion for currency '{self.currency}'")
        # CRC has no cents — quantize to integer colones
        converted = (self.amount * fx_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return Money(converted, "CRC")

    def convert_to(self, target_currency: str, fx_rate: Decimal) -> Money:
        """Convert to target_currency using fx_rate (₡ per USD)."""
        if target_currency == "USD":
            return self.to_usd(fx_rate)
        if target_currency == "CRC":
            return self.to_crc(fx_rate)
        raise ValueError(f"Unsupported target currency: {target_currency}")

    def is_zero(self) -> bool:
        return self.amount == Decimal("0")

    def is_positive(self) -> bool:
        return self.amount > Decimal("0")

    def is_negative(self) -> bool:
        return self.amount < Decimal("0")


# ── Module-level helpers ──────────────────────────────────────────────────────

def _require_same_currency(a: Money, b: Money, op: str) -> None:
    if a.currency != b.currency:
        raise ValueError(
            f"Cannot {op} {a.currency} and {b.currency} without explicit FX conversion. "
            "Call .to_usd() or .to_crc() first."
        )


def convert(
    amount: Decimal,
    from_currency: str,
    to_currency: str,
    fx_rate: Decimal | None,
) -> Decimal:
    """Convert amount between CRC and USD. fx_rate = ₡ per 1 USD.

    Used by routers and core functions that work with raw Decimal amounts.
    Prefer Money.convert_to() for object-oriented code.
    """
    if from_currency == to_currency:
        return amount
    if fx_rate is None:
        raise ValueError("FX rate required for currency conversion")
    m = Money(amount, from_currency)
    return m.convert_to(to_currency, fx_rate).amount


def sum_money(items: list[Money], currency: str) -> Money:
    """Sum a list of same-currency Money values. Raises if currencies differ."""
    total = Money(Decimal("0"), currency)
    for item in items:
        total = total + item
    return total


def fx_for_date(transaction_date: date, household_fx_ref: Decimal | None = None) -> Decimal:
    """Return the FX rate (₡ per USD) for a given date.

    Phase 0-1: returns the household reference rate (default ₡470/USD).
    Phase 3+: will query a stored FX rate table for historical accuracy.

    The pilot used a fixed rate of ₡470/USD throughout Jun–Aug 2026.
    """
    # Use household-specific reference rate if provided; otherwise fall back to pilot default
    if household_fx_ref is not None:
        return household_fx_ref
    # Pilot default — representative rate for Jun 2026
    return Decimal("470")
