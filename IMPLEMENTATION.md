# IMPLEMENTATION.md — Fases y checklist

Guía paso a paso para Claude Code. Construir **en orden de fase**. Dentro de cada feature: `core` + test unitario → endpoint + test de componente → `pnpm gen:api` → web → mobile → marcar casilla.

**Estado:** ⬜ pendiente · 🟡 en progreso · ✅ hecho · 🧪 probado
**Capa:** core (Python) · api (FastAPI) · web · mobile · infra

> Regla: código y BD en inglés; textos de usuario en español. Cada feature debe pasar los 6 criterios de prueba de `../FUNCIONALIDADES_APP.md`.

---

## Fase 0 — Cimientos (empezar aquí)

| # | Tarea | Capa | Estado |
|---|---|---|---|
| 0.1 | Monorepo + tooling (uv, pnpm, turbo, ruff, mypy) | infra | ✅ |
| 0.2 | Firebase Auth + Emulator Suite corriendo local | infra | ✅ |
| 0.3 | Esquema Firestore + `firestore.rules` (inglés) | api | ✅ |
| 0.4 | Modelos Pydantic / `app/models/schemas.py` | api | ✅ |
| 0.5 | `scripts/seed.py` con el caso Fau & Mari | api | ✅ |
| 0.6 | CI: lint + `pytest` + `pip-audit`/`npm audit` | infra | ✅ |
| 0.7 | `GET /health` + `pnpm gen:api` funcionando | api | ✅ |

---

## Fase 1 — MVP (P0)

| # | Funcionalidad | Capa | Estado |
|---|---|---|---|
| 1.1 | `core.money` (Money, FX por fecha) + tests | core | ✅ |
| 1.2 | `core.pockets` (saldos, no-cruce de moneda) + tests | core | ✅ |
| 1.3 | `core.plan` (construir/validar baseline) + tests | core | ✅ |
| 1.4 | `core.matching` (suggest_line, abonos parciales) + tests | core | ✅ |
| 1.5 | `core.comparison` (compare_plan_actual) + tests | core | ✅ |
| 1.6 | Endpoints `/plan/validate`, `/transactions`, `/comparison/{month}`, `/debts/avalanche` + tests de componente | api | ✅ |
| 1.7 | Onboarding / ingesta de datos | web | ⬜ |
| 1.8 | Vista del plan baseline | web | ⬜ |
| 1.9 | Registrar transacciones (ledger real) | web | ⬜ |
| 1.10 | Emparejamiento real ↔ plan (UI) | web | ⬜ |
| 1.11 | Comparativa Plan vs Real | web | ⬜ |
| 1.12 | Calendario de pagos + recordatorios | web | ⬜ |
| 1.13 | Deudas (avalancha) | web | ⬜ |
| 1.14 | Transferencia entre bolsillos | web | ⬜ |
| 1.15 | Chat IA básico (`/chat`, tool-use → core) | api+web | ⬜ |
| 1.16 | Paridad mobile de lo anterior | mobile | ⬜ |

---

## Fase 2 — Experiencia (P1)

| # | Funcionalidad | Capa | Estado |
|---|---|---|---|
| 2.1 | `core.simulation` (simulate_expense, semáforo) + tests | core | ✅ |
| 2.2 | `core.leisure` (topes, disponible, split 50/50) + tests | core | ✅ |
| 2.3 | `core.emergency_fund` + `core.goals` + tests | core | ✅ |
| 2.4 | Chequeo previo al gasto (guardrail) | api+web | ⬜ |
| 2.5 | Simulación / proyección (`/simulate`) + test componente | api | ✅ |
| 2.6 | Aprobación multi-usuario + versionado de plan (`/propose`, `/approve`) | api | ✅ |
| 2.7 | Presupuesto de ocio (`/leisure/status`) + test componente | api | ✅ |
| 2.8 | Fondo de emergencia (meta/prioridad) | web | ⬜ |
| 2.9 | Metas de ahorro y viajes (sinking funds) | web | ⬜ |
| 2.10 | Alertas proactivas (`core.alerts` + `GET /alerts`) + tests | api | ✅ |
| 2.11 | IA en la UI (explica al editar el plan) | web | ⬜ |
| 2.12 | `POST /close-month` (archiva plan + reporte) | api | ✅ |
| 2.13 | Reporte de cierre mensual (CloseMonthResponse) | api | ✅ |
| 2.14 | Paridad mobile | mobile | ⬜ |

---

## Fase 3 — Escala (P2)

| # | Funcionalidad | Capa | Estado |
|---|---|---|---|
| 3.1 | Proyección de pago de deuda (payoff) | core+web | ⬜ |
| 3.2 | Categorización automática con IA | api | ⬜ |
| 3.3 | RAG sobre historial (consultas en lenguaje natural) | api | ⬜ |
| 3.4 | OCR de recibos | api+mobile | ⬜ |
| 3.5 | Sincronización bancaria (open banking) | api | ⬜ |
| 3.6 | Gamificación | web+mobile | ⬜ |

---

*Al completar una fila, cambiar el estado y, si aplica, anotar el commit/PR. La Fase N+1 no arranca hasta que la Fase N esté en ✅/🧪 en sus filas core/api.*
