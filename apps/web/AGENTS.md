# AGENTS.md — HogarClaro Web UI

Instrucciones para Codex y otros agentes de desarrollo que trabajen en esta carpeta.

---

## 0. Ubicación y alcance (leer primero)

- Esta web vive en **`finanzas-app/apps/web/`**, dentro del monorepo — NO es un repo suelto.
- **Codex es dueño solo de `apps/web/`.** No edites `apps/api` (backend) ni `packages/api-client` (se genera).
- **El backend ya está definido y Codex NO lo construye:** Core API en **Python + FastAPI** (`finanzas-app/apps/api`), base de datos **Firestore**, auth **Firebase Auth**. La integración se hace consumiendo el contrato vía **`packages/api-client`** (cliente TS del OpenAPI). Nada de NestJS / PostgreSQL / Clerk.
- **Fases tempranas: standalone con mock data.** La lógica en `src/lib/finance` valida la UX y las reglas de dinero sin backend; **espeja el contrato** y, en la integración, se respalda con llamadas a la Core API (que es la fuente de verdad en producción).
- **Documentos:** los específicos de la web están en `apps/web/docs/`; los compartidos (`FUNCIONALIDADES_APP.md`, `ARQUITECTURA_PLAN.md`, `PROPUESTA_VISUAL_APP.md`) en la **raíz del proyecto** (ver `docs/FUNCIONALIDADES_APP.md` para la ruta).
- **Mockups de referencia de diseño (v1):** en `apps/web/docs/mockups-web/`. Úsalos como guía visual para el dashboard y pantallas P0/P1.

---

## 1. Producto

HogarClaro es una app web de finanzas personales y familiares.

El producto ayuda a parejas/familias a saber:

- cuánto dinero tienen disponible,
- qué deben pagar,
- cuándo deben pagarlo,
- qué gasto rompe o no rompe el plan,
- qué deuda conviene atacar primero,
- cómo van contra el plan original.

La experiencia debe transmitir:

```txt
calma + claridad + control + confianza
```

No debe sentirse como una app bancaria fría ni como un dashboard saturado.

---

## 2. Archivos que debes leer antes de modificar código

Antes de implementar cualquier feature, revisa:

```txt
docs/WEB_UI_CODEX_IMPLEMENTATION_GUIDE.md
docs/FUNCIONALIDADES_APP.md
```

Si existen, también revisa:

```txt
docs/PRODUCT_GUIDELINES.md
docs/UI_DECISIONS.md
```

---

## 3. Reglas financieras obligatorias

Estas reglas no se negocian.

### 3.1 Monedas

- CRC y USD no se mezclan automáticamente.
- No sumes montos de diferentes monedas sin conversión explícita.
- Si hay conversión, debe existir FX rate guardado por transacción.

### 3.2 Bolsillos

- Cada bolsillo pertenece a una persona o al hogar.
- Cada bolsillo tiene una moneda.
- Los saldos de bolsillos no se cruzan automáticamente.
- Las transferencias entre bolsillos deben registrarse explícitamente.

### 3.3 Plan baseline

- El plan baseline es la fuente de comparación.
- El baseline no se modifica automáticamente.
- Las transacciones reales se comparan contra el baseline, pero no lo mutan.
- Cambios al baseline requieren flujo de edición/aprobación.

### 3.4 Real ledger

- El Real representa transacciones efectivas.
- El Real puede emparejarse con líneas del Plan.
- Una línea del Plan puede tener varios pagos reales parciales.
- Una transacción no emparejada debe marcarse como fuera de plan.

### 3.5 Deudas

- La estrategia avalancha ordena deudas por tasa de interés de mayor a menor.
- Las deudas sin tasa deben ir después de las deudas con tasa conocida, salvo regla explícita.
- La deuda prioritaria debe explicar por qué es prioritaria.

---

## 4. Reglas UX/UI

### 4.1 Estilo

Usa una estética fintech limpia, moderna y calmada:

- fondos claros,
- mucho espacio en blanco,
- tarjetas redondeadas,
- bordes sutiles,
- sombras muy suaves,
- tipografía sans-serif,
- iconografía lineal,
- paleta limitada.

### 4.2 Colores

Usa la paleta definida en `WEB_UI_CODEX_IMPLEMENTATION_GUIDE.md`.

No agregues colores nuevos sin una razón explícita.

Uso semántico:

```txt
Indigo: marca y CTA principal
Teal/green: positivo / dentro del plan
Amber: revisar / advertencia suave
Soft red: atraso / riesgo real
Neutral: estructura y datos secundarios
```

### 4.3 Saturación

Evita saturación visual.

En el dashboard principal:

- máximo 7 bloques grandes,
- máximo 4 tarjetas de métrica,
- máximo 3 estados de color activos,
- máximo 1 alerta fuerte,
- máximo 1 acción principal clara.

### 4.4 IA en la UI

La IA debe sentirse integrada, no invasiva.

Usa IA para:

- pulso financiero del mes,
- recomendación principal,
- explicación de desviaciones,
- chequeo previo al gasto,
- alertas inteligentes.

Evita repetir etiquetas como:

```txt
IA:
AI:
Copiloto:
```

en todas las tarjetas.

Preferir copy natural:

```txt
Proyección: cerrás dentro del plan si mantenés este ritmo.
```

---

## 5. Reglas de arquitectura frontend

Stack recomendado:

```txt
Next.js
React
TypeScript
Tailwind CSS
Recharts
React Hook Form
Zod
Vitest
```

Reglas:

- Componentes visuales reutilizables en `src/components/ui`.
- Layout en `src/components/layout`.
- Componentes específicos de dashboard en `src/components/dashboard`.
- Componentes financieros en `src/components/finance`.
- Tipos en `src/types`.
- Mock data en `src/data`.
- Lógica financiera pura en `src/lib/finance`.
- Tests en `src/tests`.

No mezcles lógica financiera compleja dentro de componentes React.

---

## 6. Reglas para trabajar con Codex

Trabaja en cambios pequeños, revisables y seguros.

Preferir tareas tipo:

```txt
Implement Dashboard static UI
```

en vez de:

```txt
Build the full app
```

Antes de codificar:

1. Lee la documentación.
2. Identifica la fase o versión.
3. Resume brevemente qué vas a cambiar.
4. Implementa.
5. Ejecuta lint/tests si existen.
6. No modifiques pantallas no relacionadas.

---

## 7. Versiones del producto

### V0.1 — Setup

- Next.js + TypeScript.
- Tailwind.
- ESLint / Prettier.
- Estructura base.
- Documentación local.

### V0.2 — Design System

- AppShell.
- Sidebar.
- TopBar.
- Card.
- Button.
- Badge.
- StatusChip.
- MetricCard.

### V0.3 — Dashboard UI estático

- Resumen del hogar.
- Pulso financiero del mes.
- 4 métricas clave.
- Plan vs Real chart.
- Próximos pagos.
- Mejor acción sugerida.
- Requiere atención.

### V0.4 — Mock data tipado

- Members.
- Pockets.
- Plan.
- Real transactions.
- Payments.
- Debts.
- AI insights.

### V0.5 — Lógica financiera

- Running balance.
- Plan vs Real.
- Matching parcial.
- Out-of-plan.
- Debt avalanche.
- Guardrail.

### V0.6 — Tests

- Vitest.
- Tests de reglas financieras críticas.

### V1.0 — MVP P0

Debe cubrir todas las funcionalidades P0 del backlog.

### V1.1 — UX diferencial P1

Debe cubrir chequeo de gasto, aprobación, ocio/gustos, alertas proactivas, IA integrada y reporte mensual.

### V2.0 — Escala

Incluye OCR, open banking, RAG, categorización automática y background AI real.

---

## 8. Prohibiciones

No hagas esto:

- No mezcles CRC y USD.
- No escondas conversiones.
- No cambies el baseline automáticamente.
- No hardcodees datos financieros críticos en componentes.
- No crees un backend si no fue pedido.
- No agregues muchas tarjetas solo para llenar espacio.
- No uses rojo fuerte para advertencias menores.
- No implementes P2 antes de P0.
- No pongas IA como protagonista visual de toda la pantalla.
- No elimines tests existentes sin reemplazarlos.
- No cambies reglas financieras para facilitar UI.

---

## 9. Definition of Done

Una tarea está lista cuando:

- Respeta reglas financieras.
- Usa componentes del design system.
- No introduce saturación visual.
- Está en español.
- Tiene datos tipados.
- Tiene tests si toca lógica financiera.
- Pasa lint.
- Pasa tests existentes.
- Es responsive cuando aplica.
- La acción principal es clara.
- La UI transmite calma y control.

---

## 10. Prompt base recomendado

Cuando se pida una tarea nueva, usar este contexto:

```txt
You are working on HogarClaro, a family finance web app.

Read AGENTS.md and docs/WEB_UI_CODEX_IMPLEMENTATION_GUIDE.md before coding.

Respect these core rules:
- CRC and USD must never be mixed automatically.
- Pockets are separated by person and currency.
- The Plan baseline is immutable unless explicitly approved.
- Real transactions are compared against the Plan but do not mutate it.
- The UI must be clean, minimal, calm and trustworthy.
- AI should be a subtle intelligence layer, not visual noise.

Work in small, reviewable changes.
Do not implement backend unless explicitly requested.
```
