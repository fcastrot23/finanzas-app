"""FastAPI entrypoint — the financial Core API. English only.

Run locally:  cd apps/api && uvicorn main:app --reload
OpenAPI:      http://localhost:8000/openapi.json  →  pnpm gen:api  →  packages/api-client
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    chat,
    close_month,
    comparison,
    debts,
    health,
    leisure,
    plans,
    simulation,
    transactions,
)

app = FastAPI(
    title="HogarClaro — Core API",
    version="0.1.0",
    description=(
        "Deterministic financial engine for HogarClaro. "
        "The LLM narrates; this API computes. "
        "All money math lives in app/core (Python, pytest-tested)."
    ),
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_allowed_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173",  # Next.js dev / Vite dev
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(plans.router)
app.include_router(transactions.router)
app.include_router(comparison.router)
app.include_router(simulation.router)
app.include_router(debts.router)
app.include_router(leisure.router)
app.include_router(close_month.router)
app.include_router(chat.router)
