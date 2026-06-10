"""Pydantic models — request/response schemas for every endpoint.

These drive the OpenAPI schema → packages/api-client (TS generated client).
Field names are in English; user-facing text (descriptions) may reference Spanish UX concepts.
The LLM never computes money — these models carry the inputs/outputs of deterministic core functions.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

# ── Enums ─────────────────────────────────────────────────────────────────────

class Currency(str, Enum):
    CRC = "CRC"
    USD = "USD"


class PlanStatus(str, Enum):
    draft = "draft"
    proposed = "proposed"
    active = "active"
    archived = "archived"


class LineType(str, Enum):
    income = "income"
    expense = "expense"
    debt = "debt"
    leisure = "leisure"
    transfer = "transfer"


class TxStatus(str, Enum):
    in_plan = "in_plan"
    out_of_plan = "out_of_plan"


class LeisureType(str, Enum):
    individual = "individual"
    household = "household"


class IncomeFrequency(str, Enum):
    monthly = "monthly"
    biweekly = "biweekly"
    weekly = "weekly"
    seasonal = "seasonal"


class TrafficLight(str, Enum):
    green = "green"
    amber = "amber"
    red = "red"


class DebtType(str, Enum):
    credit_card = "credit_card"
    mortgage = "mortgage"
    auto = "auto"
    personal = "personal"
    other = "other"


# ── Shared primitives ─────────────────────────────────────────────────────────

PositiveDecimal = Annotated[Decimal, Field(gt=0)]
NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]


class Money(BaseModel):
    """Immutable money value — amount + currency. Core never mixes currencies."""
    amount: Decimal = Field(description="Exact decimal amount (never a float)")
    currency: Currency


class SplitEntry(BaseModel):
    """One member's share of a household expense."""
    uid: str
    amount: Decimal


# ── Domain models (read — what comes back from Firestore) ─────────────────────

class Household(BaseModel):
    id: str
    name: str
    members: list[str] = Field(description="List of Firebase uids")
    base_currency: Currency = Currency.CRC
    fx_ref: Decimal | None = Field(
        None, description="Reference exchange rate CRC/USD used when fx is unknown"
    )


class User(BaseModel):
    uid: str
    name: str
    email: str
    household_id: str
    role: str = "member"


class Pocket(BaseModel):
    id: str
    household_id: str
    owner_uid: str | None = Field(None, description="null = shared household pocket")
    currency: Currency
    name: str


class Income(BaseModel):
    id: str
    household_id: str
    pocket_id: str
    owner_uid: str | None = None
    amount: Decimal
    currency: Currency
    frequency: IncomeFrequency
    pay_day: int = Field(description="Day of month (1-31); for biweekly: first pay day")
    pay_day_2: int | None = Field(None, description="Second pay day for biweekly")
    seasonal: bool = False
    concept: str


class FixedExpense(BaseModel):
    id: str
    household_id: str
    concept: str
    amount: Decimal
    currency: Currency
    due_day: int = Field(description="Day of month when expense is due")
    category: str


class Debt(BaseModel):
    id: str
    household_id: str
    owner_uid: str | None = None
    creditor: str
    type: DebtType
    balance: Decimal
    currency: Currency
    rate: Decimal = Field(description="Annual interest rate as decimal, e.g. 0.23 = 23%")
    payment: Decimal = Field(description="Minimum monthly payment")
    priority: int = Field(description="Avalanche order (1 = highest rate = pay first)")


class PlanLine(BaseModel):
    id: str
    date: date
    pocket_id: str
    concept: str
    amount: Decimal
    currency: Currency
    category: str
    type: LineType


class Plan(BaseModel):
    id: str
    household_id: str
    version: int = 1
    status: PlanStatus
    period: dict[str, date] = Field(description='{"from": date, "to": date}')
    approvals: dict[str, bool] = Field(
        default_factory=dict,
        description="uid → bool; all True = proposed → active",
    )
    lines: list[PlanLine] = Field(default_factory=list)


class TxSplit(BaseModel):
    uid: str
    amount: Decimal


class Transaction(BaseModel):
    id: str
    household_id: str
    pocket_id: str
    date: date
    concept: str
    amount: Decimal
    currency: Currency
    fx: Decimal | None = Field(None, description="Exchange rate at time of transaction")
    plan_line_id: str | None = None
    status: TxStatus
    category: str
    split: list[TxSplit] = Field(default_factory=list)
    created_at: datetime | None = None


class LeisureBudget(BaseModel):
    id: str
    household_id: str
    type: LeisureType
    owner_uid: str | None = Field(None, description="null for household type")
    monthly_cap: Decimal
    weekly_cap: Decimal | None = None
    spent: Decimal = Decimal("0")

    @property
    def available(self) -> Decimal:
        return self.monthly_cap - self.spent


class Goal(BaseModel):
    id: str
    household_id: str
    name: str
    target: Decimal
    saved: Decimal = Decimal("0")
    target_date: date | None = None
    currency: Currency = Currency.CRC


# ── Request bodies ────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    pocket_id: str
    date: date
    concept: str
    amount: PositiveDecimal
    currency: Currency
    fx: Decimal | None = None
    plan_line_id: str | None = None
    category: str = "general"
    split: list[TxSplit] = Field(default_factory=list)


class TransactionUpdate(BaseModel):
    plan_line_id: str | None = None
    category: str | None = None
    split: list[TxSplit] | None = None


class PlanCreate(BaseModel):
    period_from: date
    period_to: date
    lines: list[PlanLineCreate]


class PlanLineCreate(BaseModel):
    date: date
    pocket_id: str
    concept: str
    amount: PositiveDecimal
    currency: Currency
    category: str = "general"
    type: LineType


# Fix forward reference
PlanCreate.model_rebuild()


class SimulateRequest(BaseModel):
    """Propose an out-of-plan expense; core returns traffic-light + trade-off."""
    pocket_id: str
    amount: PositiveDecimal
    currency: Currency
    concept: str
    proposed_date: date
    fx: Decimal | None = Field(None, description="Override FX rate for conversion")


class ApprovalRequest(BaseModel):
    uid: str
    approved: bool


# ── Response bodies ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str


class SimulateResponse(BaseModel):
    light: TrafficLight
    feasible: bool
    sacrifice: str | None = Field(
        None, description="What gets deferred or reduced to fund this expense"
    )
    source: str | None = Field(
        None, description="Which pocket/line absorbs the expense"
    )
    detail: str = Field(description="Human-readable explanation (narrated by the agent)")


class DeviationItem(BaseModel):
    pocket_id: str
    pocket_name: str
    currency: Currency
    planned: Decimal
    actual: Decimal
    delta: Decimal
    delta_pct: Decimal | None = None


class ComparisonResponse(BaseModel):
    month: str = Field(description="YYYY-MM")
    household_id: str
    items: list[DeviationItem]
    total_planned: Decimal
    total_actual: Decimal
    total_delta: Decimal


class AvalancheEntry(BaseModel):
    debt_id: str
    creditor: str
    balance: Decimal
    currency: Currency
    rate: Decimal
    payment: Decimal
    priority: int
    months_to_payoff: int | None = None


class AvalancheResponse(BaseModel):
    household_id: str
    debts: list[AvalancheEntry]
    total_balance_usd: Decimal = Field(description="All balances converted to USD")


class MatchSuggestion(BaseModel):
    transaction_id: str
    suggested_plan_line_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class LeisureStatus(BaseModel):
    household_id: str
    period_start: date
    period_end: date
    individual: list[dict]  # [{uid, name, monthly_cap, weekly_cap, spent, available}]
    household_budget: dict | None = None  # {monthly_cap, weekly_cap, spent, available}


class PlanValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: str = Field(description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    household_id: str
    messages: list[ChatMessage]
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    tool_calls_made: list[str] = Field(default_factory=list)
