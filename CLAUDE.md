# CLAUDE.md — Guía para Claude Code

Repo de la app de finanzas personales y familiares con IA. Lee también, en la raíz del proyecto, `../ARQUITECTURA_PLAN.md`, `../FUNCIONALIDADES_APP.md`, `IMPLEMENTATION.md` y `VERSIONS.md`.

## Principios (no negociables)
- **Código y base de datos en inglés.** Variables, funciones, módulos, endpoints, colecciones y campos de Firestore en inglés. Solo el texto para el usuario (UI, mensajes del agente) va en español.
- **El LLM nunca calcula dinero.** Toda la matemática vive en `apps/api/app/core/` (Python puro, testeado). El agente solo decide qué función llamar y narra.
- **Los frontends no duplican lógica financiera.** Web y mobile llaman la Core API; no recalculan nada.
- **El core es la fuente de verdad** expuesta como API; el contrato es el OpenAPI → cliente TS en `packages/api-client`.
- **Local-first.** Todo corre con el Firebase Emulator Suite antes de la nube.

## Estructura
- `apps/api/` — Core API (Python · FastAPI): `app/core` (lógica pura), `app/routers` (REST), `app/ai` (agente Claude), `app/db`, `app/security`, `app/models`, `tests/`.
- `apps/web/` — React + Vite. `apps/mobile/` — React Native + Expo.
- `packages/api-client/` — cliente TS autogenerado desde el OpenAPI.

## Orden de trabajo por feature
1. Función en `app/core` (Python) + **test unitario** (`tests/unit`) que reproduce un caso real del piloto.
2. Endpoint en `app/routers` + **test de componente** (`tests/component`, TestClient + emulador + LLM grabado).
3. Regenerar el cliente: `pnpm gen:api`.
4. UI web, luego mobile.
5. Marcar la casilla en `IMPLEMENTATION.md`.

## Comandos
```
cd apps/api && uv sync          # deps Python
firebase emulators:start        # Auth + Firestore locales
uvicorn apps.api.main:app --reload
pnpm gen:api                    # OpenAPI -> packages/api-client
pnpm --filter web dev           # web
pnpm --filter mobile start      # mobile (Expo)
pytest                          # tests (unit + component) en apps/api
python scripts/seed.py          # siembra el caso Fau & Mari
```

## Definición de hecho
- Función `core` con tests que reproducen un caso del piloto (verde).
- Endpoint con su esquema OpenAPI y **test de componente** verde.
- Cliente `api-client` regenerado.
- Pasa los 6 criterios de prueba de `../FUNCIONALIDADES_APP.md`.
- Casilla marcada en `IMPLEMENTATION.md`.

## No hacer
- Lógica financiera en UI o en el prompt del LLM.
- Exponer `ANTHROPIC_API_KEY` al cliente.
- Escribir `plans` activos desde el cliente (solo backend, con aprobación).
- Nombres en español en código o BD.

## Arrancar por
Fase 0 completa (ver `IMPLEMENTATION.md`) con `seed.py` funcionando, antes de cualquier feature.

## Trabajo en paralelo con Codex (importante)
- **Claude Code es dueño de:** arquitectura, `apps/api`, `infra/`, `scripts/`, `firestore.rules`, generación de `packages/api-client`. **No edites `apps/web`** — esa es de Codex.
- **Codex desarrolla la web contra un MOCK del contrato**, no contra tu core. Por eso tu trabajo en el core (aunque sea inestable en fases tempranas) **no debe afectarlo**.
- **Prioridad en Fase 0/1: contract-first.** Definí primero los **modelos Pydantic + firmas de endpoints** para que el `openapi.json` y el `api-client` existan ya, aunque el core interno sea stub. Eso desbloquea a Codex de inmediato.
- **Los cambios de contrato (OpenAPI) son deliberados y se anuncian** (regenerar `api-client` + nota en el PR). Nunca rompas el contrato como efecto secundario de refactorizar el core.
- Ver `../ARQUITECTURA_PLAN.md` §15 para el detalle de colaboración.
