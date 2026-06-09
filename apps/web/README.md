# apps/web — Web (Next.js + React) · dueño: Codex

Frontend web de la app de finanzas. **Codex** es responsable de esta carpeta.

## Reglas de colaboración (ver ../../ARQUITECTURA_PLAN.md §15)
- **Consumir la API solo vía `packages/api-client`** (cliente TS generado del OpenAPI). No hardcodear llamadas.
- **Desarrollar contra un MOCK del contrato, no contra el core real** de Claude Code:
  - Opción A: **MSW (Mock Service Worker)** con fixtures del piloto (Fau & Mari).
  - Opción B: mock server desde el esquema → `prism mock http://localhost:8000/openapi.json`.
- **No editar `apps/api`** ni `packages/api-client` a mano (este último se regenera).
- En fases tempranas, la web corre standalone con datos mock tipados.
- La lógica financiera local vive en `src/lib/finance` como funciones puras para validar UX y reglas de dinero.
- Textos de usuario en español; nombres de código en inglés.

## Arranque (independiente del core)
```
pnpm install
pnpm --filter web dev
pnpm --filter web lint
pnpm --filter web test
```
