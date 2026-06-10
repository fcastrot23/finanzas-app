"""Seed the Firestore emulator with the Fau & Mari pilot household.

Run: FIRESTORE_EMULATOR_HOST=localhost:8080 python scripts/seed.py

Creates:
- 1 household (Fau & Mari)
- 2 users (fau, mari)
- 4 pockets (fau-usd, fau-crc, mari-crc, household-crc)
- 2 incomes (Fau Equifax biweekly USD; Mari 3M monthly CRC)
  + 1 seasonal income (Fau Hyatt USD)
- Fixed expenses (rent-equivalent, utilities, school, subscriptions, groceries)
- 9 debts ordered by avalanche (highest rate first)
- 1 active 3-month plan (Jun–Aug 2026) with lines
- June 2026 real transactions (partial — what happened in the first week)
- Leisure budgets (individual + household)

Data source: BITACORA_PROYECTO.md sessions 2–3 (2026-06-05/06).
Exchange rate reference: ₡470/USD.
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

# Allow running from repo root or scripts/ directory
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

import firebase_admin
from firebase_admin import credentials, firestore

# ── Constants ─────────────────────────────────────────────────────────────────
PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "finanzas-dev")
EMULATOR_HOST = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080")

# Household / user IDs — fixed so tests can reference them
HOUSEHOLD_ID = "hh_fau_mari"
FAU_UID = "uid_fau"
MARI_UID = "uid_mari"

# Pocket IDs
POCKET_FAU_USD = "pocket_fau_usd"
POCKET_FAU_CRC = "pocket_fau_crc"
POCKET_MARI_CRC = "pocket_mari_crc"
POCKET_HH_CRC = "pocket_hh_crc"  # shared household CRC pocket

FX_RATE = Decimal("470")  # ₡ per 1 USD (reference rate Jun 2026)


# ── Helpers ───────────────────────────────────────────────────────────────────

def usd(amount: str | float) -> str:
    return str(Decimal(str(amount)).quantize(Decimal("0.01")))


def crc(amount: str | int) -> str:
    return str(Decimal(str(amount)).quantize(Decimal("1")))


def _init() -> firestore.Client:
    os.environ.setdefault("FIRESTORE_EMULATOR_HOST", EMULATOR_HOST)
    try:
        app = firebase_admin.get_app()
    except ValueError:
        app = firebase_admin.initialize_app(options={"projectId": PROJECT_ID})
    return firestore.client(app)


# ── Seed functions ─────────────────────────────────────────────────────────────

def seed_household(db: firestore.Client) -> None:
    db.collection("households").document(HOUSEHOLD_ID).set({
        "name": "Fau & Mari",
        "members": [FAU_UID, MARI_UID],
        "baseCurrency": "CRC",
        "fxRef": str(FX_RATE),
    })
    print("  ✓ household")


def seed_users(db: firestore.Client) -> None:
    db.collection("users").document(FAU_UID).set({
        "name": "Fau",
        "email": "josue23fabricio@gmail.com",
        "householdId": HOUSEHOLD_ID,
        "role": "member",
    })
    db.collection("users").document(MARI_UID).set({
        "name": "Mari",
        "email": "mari@hogarclaropilot.local",
        "householdId": HOUSEHOLD_ID,
        "role": "member",
    })
    print("  ✓ users (fau, mari)")


def seed_pockets(db: firestore.Client) -> None:
    pockets = [
        {
            "id": POCKET_FAU_USD,
            "householdId": HOUSEHOLD_ID,
            "ownerUid": FAU_UID,
            "currency": "USD",
            "name": "Fau — dólares",
        },
        {
            "id": POCKET_FAU_CRC,
            "householdId": HOUSEHOLD_ID,
            "ownerUid": FAU_UID,
            "currency": "CRC",
            "name": "Fau — colones",
        },
        {
            "id": POCKET_MARI_CRC,
            "householdId": HOUSEHOLD_ID,
            "ownerUid": MARI_UID,
            "currency": "CRC",
            "name": "Mari — colones",
        },
        {
            "id": POCKET_HH_CRC,
            "householdId": HOUSEHOLD_ID,
            "ownerUid": None,
            "currency": "CRC",
            "name": "Hogar — colones compartidos",
        },
    ]
    for p in pockets:
        pid = p.pop("id")
        db.collection("pockets").document(pid).set(p)
    print(f"  ✓ pockets ({len(pockets)})")


def seed_incomes(db: firestore.Client) -> None:
    incomes = [
        # Fau Equifax — biweekly USD (days 14 and 29)
        {
            "id": "inc_fau_equifax",
            "householdId": HOUSEHOLD_ID,
            "pocketId": POCKET_FAU_USD,
            "ownerUid": FAU_UID,
            "amount": usd("2018.65"),
            "currency": "USD",
            "frequency": "biweekly",
            "payDay": 14,
            "payDay2": 29,
            "seasonal": False,
            "concept": "Equifax — salario neto",
        },
        # Fau Hyatt — seasonal, ~$4,300/month when active (Deel, $5 fee/transfer)
        {
            "id": "inc_fau_hyatt",
            "householdId": HOUSEHOLD_ID,
            "pocketId": POCKET_FAU_USD,
            "ownerUid": FAU_UID,
            "amount": usd("4295"),  # 4300 - 5 fee
            "currency": "USD",
            "frequency": "monthly",
            "payDay": 15,
            "payDay2": None,
            "seasonal": True,
            "concept": "Hyatt — consultoría Deel (estacional)",
        },
        # Mari 3M — monthly CRC (day 25)
        {
            "id": "inc_mari_3m",
            "householdId": HOUSEHOLD_ID,
            "pocketId": POCKET_MARI_CRC,
            "ownerUid": MARI_UID,
            "amount": crc("1311667"),
            "currency": "CRC",
            "frequency": "monthly",
            "payDay": 25,
            "payDay2": None,
            "seasonal": False,
            "concept": "3M GSC CR — salario neto",
        },
    ]
    for inc in incomes:
        iid = inc.pop("id")
        db.collection("incomes").document(iid).set(inc)
    print(f"  ✓ incomes ({len(incomes)})")


def seed_fixed_expenses(db: firestore.Client) -> None:
    # Monthly fixed expenses; amounts from pilot session 2
    fixed = [
        # Life expenses ≈ ₡1,344,364 + $183/month
        {
            "id": "fexp_groceries",
            "householdId": HOUSEHOLD_ID,
            "concept": "Supermercado / alimentación",
            "amount": crc("400000"),
            "currency": "CRC",
            "dueDay": 1,
            "category": "groceries",
        },
        {
            "id": "fexp_school",
            "householdId": HOUSEHOLD_ID,
            "concept": "Escuela (mensualidad)",
            "amount": crc("120000"),
            "currency": "CRC",
            "dueDay": 5,
            "category": "education",
        },
        {
            "id": "fexp_utilities",
            "householdId": HOUSEHOLD_ID,
            "concept": "Servicios públicos (luz, agua, internet)",
            "amount": crc("150000"),
            "currency": "CRC",
            "dueDay": 10,
            "category": "utilities",
        },
        {
            "id": "fexp_transport",
            "householdId": HOUSEHOLD_ID,
            "concept": "Combustible y transporte",
            "amount": crc("200000"),
            "currency": "CRC",
            "dueDay": 1,
            "category": "transport",
        },
        {
            "id": "fexp_health",
            "householdId": HOUSEHOLD_ID,
            "concept": "Salud (médico, farmacia)",
            "amount": crc("100000"),
            "currency": "CRC",
            "dueDay": 1,
            "category": "health",
        },
        {
            "id": "fexp_phone",
            "householdId": HOUSEHOLD_ID,
            "concept": "Teléfonos",
            "amount": crc("80000"),
            "currency": "CRC",
            "dueDay": 15,
            "category": "utilities",
        },
        {
            "id": "fexp_subscriptions_usd",
            "householdId": HOUSEHOLD_ID,
            "concept": "Suscripciones (Spotify, streaming, etc.)",
            "amount": usd("43"),
            "currency": "USD",
            "dueDay": 1,
            "category": "subscriptions",
        },
        {
            "id": "fexp_transfer_mari",
            "householdId": HOUSEHOLD_ID,
            "concept": "Transferencia mensual Fau → Mari (gastos hogar)",
            "amount": crc("648000"),
            "currency": "CRC",
            "dueDay": 1,
            "category": "transfer",
        },
        {
            "id": "fexp_usd_expenses",
            "householdId": HOUSEHOLD_ID,
            "concept": "Gastos USD varios (life expenses USD portion)",
            "amount": usd("140"),
            "currency": "USD",
            "dueDay": 1,
            "category": "general",
        },
    ]
    for fe in fixed:
        fid = fe.pop("id")
        db.collection("fixedExpenses").document(fid).set(fe)
    print(f"  ✓ fixedExpenses ({len(fixed)})")


def seed_debts(db: firestore.Client) -> None:
    # Debts ordered by avalanche (highest rate first)
    # Data from pilot session 2; total ≈ $321,134 (guaranteed $194,638 + consumer $126,496)
    debts = [
        # Consumer debts — highest rates first (avalanche priority)
        {
            "id": "debt_bac_fau",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": FAU_UID,
            "creditor": "BAC — tarjeta Fau",
            "type": "credit_card",
            "balance": usd("12000"),   # approximate; 2 months behind
            "currency": "USD",
            "rate": "0.23",             # 23% annual
            "payment": usd("400"),
            "priority": 1,              # HIGHEST rate → pay first
        },
        {
            "id": "debt_davivienda_fau",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": FAU_UID,
            "creditor": "Davivienda — tarjeta Fau",
            "type": "credit_card",
            "balance": usd("8000"),
            "currency": "USD",
            "rate": "0.21",             # 21% annual
            "payment": usd("300"),
            "priority": 2,
        },
        {
            "id": "debt_davivienda_mari_crc",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": MARI_UID,
            "creditor": "Davivienda — tarjeta Mari (CRC)",
            "type": "credit_card",
            "balance": crc("2500000"),
            "currency": "CRC",
            "rate": "0.20",             # ~20% annual CRC
            "payment": crc("80000"),
            "priority": 3,
        },
        {
            "id": "debt_gollo",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": None,
            "creditor": "Gollo — crédito muebles",
            "type": "personal",
            "balance": crc("800000"),   # 2 months behind
            "currency": "CRC",
            "rate": "0.18",             # ~18% annual
            "payment": crc("70000"),
            "priority": 4,
        },
        {
            "id": "debt_coopeande_mari",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": MARI_UID,
            "creditor": "Coopeande — préstamo Mari",
            "type": "personal",
            "balance": usd("15000"),
            "currency": "USD",
            "rate": "0.12",             # cooperative rate
            "payment": usd("350"),
            "priority": 5,
        },
        {
            "id": "debt_personal_fau_1",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": FAU_UID,
            "creditor": "Préstamo personal Fau — banco",
            "type": "personal",
            "balance": usd("20000"),
            "currency": "USD",
            "rate": "0.10",
            "payment": usd("500"),
            "priority": 6,
        },
        {
            "id": "debt_personal_mari_1",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": MARI_UID,
            "creditor": "Préstamo personal Mari — banco",
            "type": "personal",
            "balance": usd("18000"),
            "currency": "USD",
            "rate": "0.09",
            "payment": usd("450"),
            "priority": 7,
        },
        # Guaranteed debts (lower rate, large balance)
        {
            "id": "debt_auto",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": FAU_UID,
            "creditor": "Banco — crédito carro",
            "type": "auto",
            "balance": usd("18000"),    # June payment missing — repossession risk
            "currency": "USD",
            "rate": "0.08",
            "payment": usd("380"),
            "priority": 8,
        },
        {
            "id": "debt_mortgage",
            "householdId": HOUSEHOLD_ID,
            "ownerUid": None,
            "creditor": "Banco — hipoteca casa",
            "type": "mortgage",
            "balance": usd("176638"),
            "currency": "USD",
            "rate": "0.055",            # ~5.5% mortgage
            "payment": usd("1200"),
            "priority": 9,
        },
    ]
    for debt in debts:
        did = debt.pop("id")
        db.collection("debts").document(did).set(debt)
    print(f"  ✓ debts ({len(debts)}, ordered by avalanche priority)")


def seed_plan(db: firestore.Client) -> None:
    """Create the 3-month baseline plan Jun–Aug 2026 (active)."""
    plan_id = "plan_jun_aug_2026_v1"

    plan_data = {
        "householdId": HOUSEHOLD_ID,
        "version": 1,
        "status": "active",
        "period": {
            "from": "2026-06-01",
            "to": "2026-08-31",
        },
        "approvals": {FAU_UID: True, MARI_UID: True},
    }
    plan_ref = db.collection("plans").document(plan_id)
    plan_ref.set(plan_data)

    # ── Plan lines ─────────────────────────────────────────────────────────────
    # June focuses on regularizing critical arrears with the $4,727 available cash.
    # Priorities: BAC Fau arrears, Davivienda Fau arrears, Carro June, Escuela May,
    # Gollo arrears, then from Jul: normal avalanche payments.

    lines = [
        # ─ JUNE INCOMES ────────────────────────────────────────────────────────
        {
            "date": "2026-06-14", "pocketId": POCKET_FAU_USD,
            "concept": "Equifax — quincena 1",
            "amount": usd("2018.65"), "currency": "USD",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-06-15", "pocketId": POCKET_FAU_USD,
            "concept": "Hyatt — pago junio",
            "amount": usd("4295"), "currency": "USD",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-06-25", "pocketId": POCKET_MARI_CRC,
            "concept": "3M GSC — salario junio",
            "amount": crc("1311667"), "currency": "CRC",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-06-29", "pocketId": POCKET_FAU_USD,
            "concept": "Equifax — quincena 2",
            "amount": usd("2018.65"), "currency": "USD",
            "category": "income", "type": "income",
        },
        # ─ JUNE CRITICAL PAYMENTS (arrears regularization) ─────────────────────
        {
            "date": "2026-06-06", "pocketId": POCKET_FAU_USD,
            "concept": "BAC tarjeta — abono atrasos May+Jun",
            "amount": usd("800"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-06-06", "pocketId": POCKET_FAU_USD,
            "concept": "Davivienda tarjeta Fau — abono atrasos May+Jun",
            "amount": usd("600"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-06-06", "pocketId": POCKET_FAU_USD,
            "concept": "Carro — cuota junio",
            "amount": usd("380"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-06-06", "pocketId": POCKET_MARI_CRC,
            "concept": "Escuela — mensualidad mayo (atrasada)",
            "amount": crc("120000"), "currency": "CRC",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-06-10", "pocketId": POCKET_MARI_CRC,
            "concept": "Gollo — abono atrasos May+Jun",
            "amount": crc("140000"), "currency": "CRC",
            "category": "debt_payment", "type": "debt",
        },
        # ─ JUNE FIXED EXPENSES ─────────────────────────────────────────────────
        {
            "date": "2026-06-05", "pocketId": POCKET_MARI_CRC,
            "concept": "Supermercado — primera compra junio",
            "amount": crc("200000"), "currency": "CRC",
            "category": "groceries", "type": "expense",
        },
        {
            "date": "2026-06-20", "pocketId": POCKET_MARI_CRC,
            "concept": "Supermercado — segunda compra junio",
            "amount": crc("200000"), "currency": "CRC",
            "category": "groceries", "type": "expense",
        },
        {
            "date": "2026-06-10", "pocketId": POCKET_MARI_CRC,
            "concept": "Servicios públicos junio",
            "amount": crc("150000"), "currency": "CRC",
            "category": "utilities", "type": "expense",
        },
        {
            "date": "2026-06-15", "pocketId": POCKET_MARI_CRC,
            "concept": "Teléfonos junio",
            "amount": crc("80000"), "currency": "CRC",
            "category": "utilities", "type": "expense",
        },
        {
            "date": "2026-06-01", "pocketId": POCKET_FAU_USD,
            "concept": "Combustible — junio",
            "amount": usd("80"), "currency": "USD",
            "category": "transport", "type": "expense",
        },
        {
            "date": "2026-06-01", "pocketId": POCKET_FAU_USD,
            "concept": "Suscripciones USD — junio",
            "amount": usd("43"), "currency": "USD",
            "category": "subscriptions", "type": "expense",
        },
        # Transfer Fau → Mari (household coverage)
        {
            "date": "2026-06-14", "pocketId": POCKET_FAU_CRC,
            "concept": "Transferencia mensual Fau → Mari",
            "amount": crc("648000"), "currency": "CRC",
            "category": "transfer", "type": "transfer",
        },
        # ─ JULY INCOMES ────────────────────────────────────────────────────────
        {
            "date": "2026-07-14", "pocketId": POCKET_FAU_USD,
            "concept": "Equifax — quincena 1 julio",
            "amount": usd("2018.65"), "currency": "USD",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-07-15", "pocketId": POCKET_FAU_USD,
            "concept": "Hyatt — pago julio",
            "amount": usd("4295"), "currency": "USD",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-07-25", "pocketId": POCKET_MARI_CRC,
            "concept": "3M GSC — salario julio",
            "amount": crc("1311667"), "currency": "CRC",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-07-29", "pocketId": POCKET_FAU_USD,
            "concept": "Equifax — quincena 2 julio",
            "amount": usd("2018.65"), "currency": "USD",
            "category": "income", "type": "income",
        },
        # ─ JULY DEBT PAYMENTS (normalized — avalanche priority) ────────────────
        {
            "date": "2026-07-05", "pocketId": POCKET_FAU_USD,
            "concept": "BAC tarjeta — cuota mínima julio",
            "amount": usd("400"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-07-05", "pocketId": POCKET_FAU_USD,
            "concept": "Davivienda tarjeta Fau — cuota mínima julio",
            "amount": usd("300"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-07-05", "pocketId": POCKET_FAU_USD,
            "concept": "Carro — cuota julio",
            "amount": usd("380"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-07-05", "pocketId": POCKET_MARI_CRC,
            "concept": "Escuela — mensualidad junio",
            "amount": crc("120000"), "currency": "CRC",
            "category": "education", "type": "expense",
        },
        {
            "date": "2026-07-05", "pocketId": POCKET_MARI_CRC,
            "concept": "Gollo — cuota julio",
            "amount": crc("70000"), "currency": "CRC",
            "category": "debt_payment", "type": "debt",
        },
        # Vacation in July — $1,000 feasible by pausing extra avalanche
        {
            "date": "2026-07-15", "pocketId": POCKET_FAU_USD,
            "concept": "Vacaciones julio — fondo viaje",
            "amount": usd("1000"), "currency": "USD",
            "category": "leisure", "type": "leisure",
        },
        # ─ AUGUST INCOMES ──────────────────────────────────────────────────────
        {
            "date": "2026-08-14", "pocketId": POCKET_FAU_USD,
            "concept": "Equifax — quincena 1 agosto",
            "amount": usd("2018.65"), "currency": "USD",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-08-15", "pocketId": POCKET_FAU_USD,
            "concept": "Hyatt — pago agosto",
            "amount": usd("4295"), "currency": "USD",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-08-25", "pocketId": POCKET_MARI_CRC,
            "concept": "3M GSC — salario agosto",
            "amount": crc("1311667"), "currency": "CRC",
            "category": "income", "type": "income",
        },
        {
            "date": "2026-08-29", "pocketId": POCKET_FAU_USD,
            "concept": "Equifax — quincena 2 agosto",
            "amount": usd("2018.65"), "currency": "USD",
            "category": "income", "type": "income",
        },
        # ─ AUGUST DEBT PAYMENTS ────────────────────────────────────────────────
        {
            "date": "2026-08-05", "pocketId": POCKET_FAU_USD,
            "concept": "BAC tarjeta — cuota mínima agosto",
            "amount": usd("400"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-08-05", "pocketId": POCKET_FAU_USD,
            "concept": "Davivienda tarjeta Fau — cuota mínima agosto",
            "amount": usd("300"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-08-05", "pocketId": POCKET_FAU_USD,
            "concept": "Carro — cuota agosto",
            "amount": usd("380"), "currency": "USD",
            "category": "debt_payment", "type": "debt",
        },
        {
            "date": "2026-08-05", "pocketId": POCKET_MARI_CRC,
            "concept": "Escuela — mensualidad julio",
            "amount": crc("120000"), "currency": "CRC",
            "category": "education", "type": "expense",
        },
    ]

    lines_ref = plan_ref.collection("lines")
    for line in lines:
        lines_ref.document().set(line)
    print(f"  ✓ plan {plan_id} ({len(lines)} lines, Jun–Aug 2026)")


def seed_transactions(db: firestore.Client) -> None:
    """Seed June 2026 real transactions (first week — what actually happened)."""
    plan_id = "plan_jun_aug_2026_v1"
    transactions = [
        # Initial cash Fau (from Equifax May-29 + Deel May)
        {
            "householdId": HOUSEHOLD_ID,
            "pocketId": POCKET_FAU_USD,
            "date": "2026-06-01",
            "concept": "Saldo inicial — Fau USD (Equifax+Deel)",
            "amount": usd("2930"),
            "currency": "USD",
            "fx": str(FX_RATE),
            "planLineId": None,
            "status": "out_of_plan",
            "category": "opening_balance",
            "split": [],
        },
        # Initial cash Mari (from 3M May-25)
        {
            "householdId": HOUSEHOLD_ID,
            "pocketId": POCKET_MARI_CRC,
            "date": "2026-06-01",
            "concept": "Saldo inicial — Mari CRC (3M mayo)",
            "amount": crc("844140"),
            "currency": "CRC",
            "fx": str(FX_RATE),
            "planLineId": None,
            "status": "out_of_plan",
            "category": "opening_balance",
            "split": [],
        },
        # Moose — household leisure expense, 50/50 split
        # (Moose: ocio hogar ₡17,900 — used as pilot case for 50/50 split)
        {
            "householdId": HOUSEHOLD_ID,
            "pocketId": POCKET_MARI_CRC,
            "date": "2026-06-05",
            "concept": "Moose — salida familiar",
            "amount": crc("17900"),
            "currency": "CRC",
            "fx": str(FX_RATE),
            "planLineId": None,
            "status": "out_of_plan",
            "category": "leisure",
            "split": [
                {"uid": FAU_UID, "amount": crc("8950")},
                {"uid": MARI_UID, "amount": crc("8950")},
            ],
        },
        # Suscripciones
        {
            "householdId": HOUSEHOLD_ID,
            "pocketId": POCKET_FAU_USD,
            "date": "2026-06-01",
            "concept": "Suscripciones USD (Spotify, etc.)",
            "amount": usd("43"),
            "currency": "USD",
            "fx": str(FX_RATE),
            "planLineId": None,
            "status": "out_of_plan",
            "category": "subscriptions",
            "split": [],
        },
    ]
    for tx in transactions:
        db.collection("transactions").document().set(tx)
    print(f"  ✓ transactions ({len(transactions)}, June 2026 — week 1)")


def seed_leisure_budgets(db: firestore.Client) -> None:
    """Leisure budgets: ₡20k/month individual, ₡30k/month household."""
    budgets = [
        {
            "id": "leisure_fau_individual",
            "householdId": HOUSEHOLD_ID,
            "type": "individual",
            "ownerUid": FAU_UID,
            "monthlyCap": crc("20000"),
            "weeklyCap": crc("5000"),
            "spent": crc("0"),
        },
        {
            "id": "leisure_mari_individual",
            "householdId": HOUSEHOLD_ID,
            "type": "individual",
            "ownerUid": MARI_UID,
            "monthlyCap": crc("20000"),
            "weeklyCap": crc("5000"),
            "spent": crc("0"),
        },
        {
            "id": "leisure_household",
            "householdId": HOUSEHOLD_ID,
            "type": "household",
            "ownerUid": None,
            "monthlyCap": crc("30000"),
            "weeklyCap": None,
            "spent": crc("17900"),  # Moose already happened
        },
    ]
    for b in budgets:
        bid = b.pop("id")
        db.collection("leisureBudgets").document(bid).set(b)
    print(f"  ✓ leisureBudgets ({len(budgets)}; household already shows Moose spend)")


def seed_goals(db: firestore.Client) -> None:
    goals = [
        {
            "id": "goal_emergency_fund",
            "householdId": HOUSEHOLD_ID,
            "name": "Fondo de emergencia (1 mes de gastos)",
            "target": usd("3000"),  # ~1 month life expenses in USD
            "saved": usd("0"),
            "targetDate": "2026-12-31",
            "currency": "USD",
        },
        {
            "id": "goal_vacation_2027",
            "householdId": HOUSEHOLD_ID,
            "name": "Vacaciones — viaje medio año 2027",
            "target": usd("3000"),
            "saved": usd("0"),
            "targetDate": "2027-06-01",
            "currency": "USD",
        },
    ]
    for g in goals:
        gid = g.pop("id")
        db.collection("goals").document(gid).set(g)
    print(f"  ✓ goals ({len(goals)})")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print(f"\nSeeding Firestore emulator at {EMULATOR_HOST} (project: {PROJECT_ID})\n")
    db = _init()

    seed_household(db)
    seed_users(db)
    seed_pockets(db)
    seed_incomes(db)
    seed_fixed_expenses(db)
    seed_debts(db)
    seed_plan(db)
    seed_transactions(db)
    seed_leisure_budgets(db)
    seed_goals(db)

    print("\n✅ Seed complete — Fau & Mari pilot household ready.\n")
    print(f"   Household ID : {HOUSEHOLD_ID}")
    print(f"   Fau UID      : {FAU_UID}")
    print(f"   Mari UID     : {MARI_UID}")
    print(f"   Plan         : plan_jun_aug_2026_v1 (active, Jun–Aug 2026)")
    print(f"   FX rate      : ₡{FX_RATE}/USD\n")


if __name__ == "__main__":
    main()
