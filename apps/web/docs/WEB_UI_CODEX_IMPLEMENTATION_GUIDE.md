# HogarClaro — Web UI Codex Implementation Guide

Documento local para guiar a Codex en el desarrollo de la Web UI/UX de **HogarClaro**, tomando como referencia el backlog funcional `FUNCIONALIDADES_APP.md` y los mockups visuales creados.

> Objetivo: convertir los mockups en una aplicación web funcional, limpia, minimalista, moderna y escalable, sin perder las reglas financieras críticas del producto.

---

## 1. Contexto del producto

HogarClaro es una app de finanzas personales y familiares para manejar dinero individual y conjunto. El modelo principal separa:

- **Personas:** Fau, Mari u otros miembros del hogar.
- **Monedas:** CRC y USD.
- **Bolsillos:** saldos separados por persona y moneda.
- **Plan baseline:** plan financiero de referencia, inicialmente a 3 meses.
- **Real ledger:** transacciones efectivas que se comparan contra el plan sin modificarlo automáticamente.
- **IA:** capa de asistencia financiera que explica, proyecta, alerta y recomienda acciones.

La experiencia debe responder siempre tres preguntas:

1. ¿Estoy bien este mes?
2. ¿Qué pago sigue?
3. ¿Qué acción concreta debería tomar?

---

## 2. Referencia funcional obligatoria

Antes de implementar cualquier pantalla, Codex debe revisar el archivo:

```txt
FUNCIONALIDADES_APP.md
```

Prioridades del backlog:

- **P0:** Núcleo / MVP. Sin esto, la app no funciona.
- **P1:** Alto valor. Define la experiencia diferencial.
- **P2:** Futuro / escala.

Las funcionalidades P0 deben guiar la arquitectura inicial:

- Bolsillos por moneda y persona.
- Multi-moneda con FX por transacción.
- Onboarding / ingesta de datos.
- Plan baseline.
- Real ledger.
- Emparejamiento Real ↔ Plan.
- Comparativa Plan vs Real.
- Calendario de pagos.
- Gestión de deudas con estrategia avalancha.
- Transferencias entre bolsillos.
- IA conversacional.

Las funcionalidades P1 deben guiar el diseño de UX:

- Chequeo previo al gasto.
- Simulación / proyección.
- Aprobación multiusuario.
- Presupuesto de ocio / gustos.
- Fondo de emergencia.
- Alertas proactivas.
- IA integrada en UI.
- Reporte mensual.

---

## 3. Recomendación técnica inicial

Para el MVP web, usar:

```txt
Frontend: Next.js + React + TypeScript
UI: Tailwind CSS + shadcn/ui o componentes propios
Charts: Recharts
Estado: Zustand o React Context al inicio
Formularios: React Hook Form + Zod
Tests unitarios: Vitest
Tests E2E futuros: Playwright
```

> **Backend (ya definido — Codex NO lo construye):** Core API en **Python + FastAPI** (`finanzas-app/apps/api`), base de datos **Firestore**, auth **Firebase Auth**. La web se integra consumiendo el contrato vía **`packages/api-client`** (cliente TS generado del OpenAPI). No usar NestJS / PostgreSQL / Clerk: esas opciones quedaron descartadas en `ARQUITECTURA_PLAN.md`.

Recomendación: **no conectar backend en la primera etapa**.

Primero construir una vertical slice con datos mock:

```txt
Dashboard
→ mock data
→ cálculo Plan vs Real
→ recomendación simulada
→ modal "¿Puedo gastar esto?"
→ tests unitarios
```

Esto valida la UX y las reglas financieras antes de meter persistencia, usuarios reales, bancos o IA real.

---

## 4. Estilo visual Web UI

La interfaz debe sentirse como una fintech moderna, pero tranquila.

### Principios visuales

- Fondo claro, blanco cálido o gris muy suave.
- Mucho espacio en blanco.
- Tarjetas redondeadas.
- Bordes sutiles.
- Sombras casi imperceptibles.
- Tipografía sans-serif geométrica y legible.
- Iconografía de línea, minimalista.
- Nada recargado.
- La interfaz debe ordenar, no abrumar.

### Paleta sugerida

```txt
Neutral base:
- Background: #F8FAFC / #FAFAF8
- Surface: #FFFFFF
- Border: #E5E7EB
- Text primary: #0F172A
- Text secondary: #64748B

Brand:
- Indigo: #2536D9 / #3046E8

Positive:
- Teal/green: #059669 / #0F9F8F

Warning:
- Amber: #D97706 / #F59E0B

Risk:
- Soft red: #DC2626 with very light backgrounds only
```

### Regla de saturación

En el dashboard principal:

- Máximo 7 bloques visuales grandes.
- Máximo 3 estados de color activos.
- No repetir badges de IA en todas partes.
- No usar rojo fuerte salvo riesgo real.
- No mostrar demasiados números a la vez.

---

## 5. Principio UX central

Cada pantalla debe responder una pregunta principal.

| Pantalla | Pregunta principal |
|---|---|
| Dashboard | ¿Estoy bien este mes y qué hago ahora? |
| Plan de pagos | ¿Qué debo pagar, cuándo y desde qué bolsillo? |
| Plan vs Real | ¿Qué se desvió del plan? |
| Chequeo de gasto | ¿Puedo gastar esto sin romper el plan? |
| Deudas | ¿Qué deuda debo atacar primero? |
| Onboarding | ¿Qué información falta para crear mi plan? |
| Aprobación | ¿Quién aprobó el plan y qué cambió? |
| Ocio / gustos | ¿Puedo disfrutar sin salirme del plan? |

---

## 6. UX de IA

La IA no debe sentirse como un chat pegado a la pantalla. Debe sentirse como una capa de inteligencia que ayuda a decidir.

### IA visible solo en lugares de alto valor

1. Pulso financiero del mes.
2. Mejor acción sugerida.
3. Alertas inteligentes.
4. Chequeo previo al gasto.
5. Explicación de desviaciones.
6. Simulaciones.

### Evitar

```txt
IA: sin riesgo
IA: recomendado
IA: atención
IA: predicción
IA: recalculado
```

Repetir “IA” en cada tarjeta genera ruido. Preferir copy humano:

```txt
Proyección: cerrás dentro del plan si mantenés este ritmo.
```

o:

```txt
Hacer un abono extra a BAC podría reducir intereses este mes.
```

---

## 7. Estructura recomendada del repo

> **Ubicación real:** la web NO es un repo suelto `hogarclaro-web/`. Vive dentro del monorepo en **`finanzas-app/apps/web/`**. El core/backend está en `finanzas-app/apps/api` (Python) y el cliente compartido en `finanzas-app/packages/api-client`. Los docs de producto compartidos (`FUNCIONALIDADES_APP.md`, `ARQUITECTURA_PLAN.md`) están en la **raíz del proyecto**; los docs específicos de la web van en `apps/web/docs/`.

```txt
finanzas-app/apps/web/      <- la web vive aquí (dentro del monorepo)
  AGENTS.md
  docs/
    WEB_UI_CODEX_IMPLEMENTATION_GUIDE.md   (este archivo)
    FUNCIONALIDADES_APP.md                 (puntero al canónico en la raíz del proyecto)
  src/
    app/
      page.tsx
      dashboard/
        page.tsx
      plan/
        page.tsx
      plan-vs-real/
        page.tsx
      debts/
        page.tsx
      onboarding/
        page.tsx
    components/
      layout/
        AppShell.tsx
        Sidebar.tsx
        TopBar.tsx
      ui/
        Button.tsx
        Card.tsx
        Badge.tsx
        StatusChip.tsx
        SectionHeader.tsx
      dashboard/
        FinancialPulse.tsx
        MetricCard.tsx
        PlanVsRealChart.tsx
        UpcomingPayments.tsx
        SuggestedActionCard.tsx
        AttentionCard.tsx
      finance/
        SpendingGuardrailModal.tsx
        DebtPriorityList.tsx
        PaymentTimeline.tsx
    data/
      mock-finance.ts
    lib/
      finance/
        currency.ts
        plan-vs-real.ts
        spending-guardrail.ts
        debt-avalanche.ts
        running-balance.ts
    types/
      finance.ts
    tests/
      finance/
        plan-vs-real.test.ts
        spending-guardrail.test.ts
        debt-avalanche.test.ts
```

---

## 8. Fases de implementación

### V0.1 — Setup técnico

Objetivo: crear base limpia del proyecto.

Entregables:

- Next.js + TypeScript.
- Tailwind CSS.
- ESLint + Prettier.
- Estructura de carpetas.
- Página inicial placeholder.
- `AGENTS.md`.
- Documentos en `/docs`.

Prompt para Codex:

```txt
Create a Next.js app with TypeScript, Tailwind CSS, ESLint and Prettier.

Use the product and UI rules from AGENTS.md and docs/WEB_UI_CODEX_IMPLEMENTATION_GUIDE.md.

Create the folder structure defined in the guide.

Do not connect any backend yet. Use mock data only.
```

Criterio de aceptación:

- La app corre localmente.
- No hay errores de lint.
- Existe estructura base.
- El diseño usa Tailwind.

---

### V0.2 — Design system

Objetivo: evitar estilos inconsistentes.

Entregables:

- Tokens visuales.
- Componentes base.
- Layout shell.
- Sidebar.
- TopBar.
- Card.
- Button.
- Badge.
- StatusChip.
- SectionHeader.

Prompt para Codex:

```txt
Implement the HogarClaro design system.

Create reusable UI components for:
- AppShell
- Sidebar
- TopBar
- Card
- Button
- Badge
- StatusChip
- SectionHeader
- MetricCard

Use a clean, calm fintech style:
warm light background, white cards, subtle borders, very soft shadows, rounded corners, indigo primary color, teal positive state, amber warning state and soft red risk state.

Do not add extra colors beyond the defined palette.
```

Criterio de aceptación:

- Todas las tarjetas comparten estilo.
- El layout se siente limpio.
- No hay saturación visual.
- La sidebar funciona en desktop.

---

### V0.3 — Dashboard estático

Objetivo: construir la primera pantalla basada en el mockup limpio.

Entregables:

- Pantalla `Resumen del hogar`.
- Sidebar.
- Header con Fau y Mari.
- Pulso financiero del mes.
- 4 tarjetas de métrica.
- Plan vs Real chart.
- Próximos pagos.
- Mejor acción sugerida.
- Requiere atención.

Prompt para Codex:

```txt
Build the Dashboard page based on the latest clean UX/UI mockup.

Screen title: "Resumen del hogar"
Subtitle: "Hogar Fau & Mari"

Add a subtle AI layer as a horizontal card:
Title: "Pulso financiero del mes"
Text: "Vas dentro del plan. Hay 2 decisiones y 1 pago que requieren atención esta semana."

Add three calm chips:
- "Dentro del plan"
- "2 decisiones"
- "1 alerta"

Add four metric cards:
1. "Colchón disponible" with "$1,275 + ₡133,575"
2. "Próximo pago" with "Carro · 2 jun · $456"
3. "Deuda prioritaria" with "Tarjeta BAC · $321,134"
4. "Ocio disponible" with "₡12,100"

Add a large "Plan vs Real" chart using Recharts.

Add a "Próximos pagos" card with:
- Carro · 02 jun · $456 · Listo
- Hipoteca · 05 jun · ₡275,000 · Próximo
- Escuela · 07 jun · ₡95,000 · Revisar

Bottom area:
- "Mejor acción sugerida"
- "Requiere atención"

Keep the screen minimal. Do not add more blocks, badges or colors.
```

Criterio de aceptación:

- En 5 segundos se entiende:
  - estado del mes,
  - próximo pago,
  - acción recomendada.
- No hay más de 7 bloques grandes.
- La IA está integrada de forma sutil.

---

### V0.4 — Mock data tipado

Objetivo: separar UI de datos.

Entregables:

- `src/types/finance.ts`
- `src/data/mock-finance.ts`

Prompt para Codex:

```txt
Create typed mock financial data for HogarClaro.

Include:
- household members: Fau and Mari
- pockets separated by person and currency
- monthly baseline plan
- real transactions
- upcoming payments
- debts ordered by interest rate
- leisure budgets
- AI insights

Important:
CRC and USD must remain separate.
Do not auto-convert currencies.
Use TypeScript interfaces in src/types/finance.ts.
Use mock records in src/data/mock-finance.ts.
```

Tipos mínimos:

```ts
export type Currency = 'CRC' | 'USD';

export type HouseholdMember = {
  id: string;
  name: string;
  defaultCurrency: Currency;
};

export type Pocket = {
  id: string;
  ownerId: string;
  currency: Currency;
  name: string;
  balance: number;
};

export type PlannedPayment = {
  id: string;
  date: string;
  concept: string;
  amount: number;
  currency: Currency;
  pocketId: string;
  status: 'planned' | 'paid' | 'review' | 'overdue';
};

export type Transaction = {
  id: string;
  date: string;
  concept: string;
  amount: number;
  currency: Currency;
  pocketId: string;
  category: string;
  source: 'manual' | 'imported';
  matchedPlanId?: string;
  outOfPlan?: boolean;
};

export type Debt = {
  id: string;
  name: string;
  type: 'consumer' | 'secured';
  balance: number;
  currency: Currency;
  interestRate?: number;
  monthlyPayment: number;
  priorityRank?: number;
};
```

Criterio de aceptación:

- Ningún componente principal usa números hardcodeados.
- Los datos salen de mock data.
- Las monedas están separadas.

---

### V0.5 — Lógica financiera inicial

Objetivo: calcular, no solo mostrar.

Entregables:

- Cálculo de saldo corriendo.
- Comparativa Plan vs Real.
- Desviación por bolsillo.
- Detección de fuera de plan.
- Ordenamiento avalancha.

Prompt para Codex:

```txt
Implement financial calculation utilities.

Create functions for:
- running balance by pocket
- plan vs real deviation
- matching real transactions to planned payments
- out-of-plan transaction detection
- avalanche debt sorting by interest rate
- upcoming payment status

Rules:
- Never mix CRC and USD automatically.
- Never mutate the plan baseline when recording real transactions.
- A planned payment can match multiple real transactions.
- Unmatched real transactions are out of plan.
```

Criterio de aceptación:

- Funciones puras.
- Sin dependencias de UI.
- Sin mutar datos de entrada.

---

### V0.6 — Tests unitarios

Objetivo: proteger reglas de dinero.

Entregables:

- Vitest.
- Tests de lógica financiera.

Prompt para Codex:

```txt
Create unit tests with Vitest for financial calculation utilities.

Test:
- CRC and USD are not mixed automatically
- running balance by pocket
- plan vs real deviation
- out-of-plan transaction detection
- partial payments matching one planned line
- avalanche debt sorting
- spending guardrail result
- baseline is not mutated by real transactions
```

Criterio de aceptación:

- Tests pasan localmente.
- Casos de borde cubiertos.
- Al menos 1 test por regla financiera crítica.

---

### V0.7 — Modal "¿Puedo gastar esto?"

Objetivo: crear el primer guardrail real.

Prompt para Codex:

```txt
Build a spending guardrail modal.

Title: "¿Puedo gastar esto?"

Fields:
- amount
- currency
- concept
- pocket
- paid by
- individual or shared

Result states:
- Green: "Cabe en tu colchón del mes"
- Amber: "Toca tu fondo de emergencia"
- Red: "Obliga a atrasar un pago del plan"

Show:
- remaining cushion
- what is sacrificed
- whether approval is required

Actions:
- "Pedir aprobación"
- "Cancelar"

Important:
This modal only evaluates impact. It must not create a real transaction.
```

Criterio de aceptación:

- El usuario entiende el impacto antes de gastar.
- El modal no se siente alarmista.
- Se puede testear la función que decide verde/ámbar/rojo.

---

### V1.0 — MVP Web UI P0

Objetivo: cubrir flujo principal del backlog P0.

Pantallas mínimas:

- Dashboard.
- Onboarding.
- Plan de pagos.
- Plan vs Real.
- Deudas.
- Transacciones.
- Bolsillos.

Criterio de aceptación:

- Todos los P0 tienen representación funcional.
- Se puede simular el caso Fau & Mari con mock data.
- No se cruzan bolsillos ni monedas.
- El baseline no se modifica solo.

---

### V1.1 — P1 UX diferencial

Objetivo: agregar valor diferencial.

Pantallas / features:

- Chequeo previo al gasto.
- Simulación.
- Aprobación multiusuario.
- Presupuesto ocio/gustos.
- Fondo de emergencia.
- Alertas proactivas.
- Reporte mensual.
- IA explicativa en UI.

Criterio de aceptación:

- Cada recomendación explica impacto.
- El usuario puede decidir antes de comprometer gasto.
- Hay trazabilidad de cambios de plan.

---

### V2.0 — Escala futura

Objetivo: preparar crecimiento.

Features futuras:

- Categorización automática.
- RAG sobre historial.
- OCR de recibos.
- Sincronización bancaria.
- Open banking.
- Gamificación.
- IA en background real.

---

## 9. Prompts maestros para Codex

### Prompt maestro de contexto

Usar al inicio de cada sesión relevante:

```txt
You are working on HogarClaro, a family finance web app.

Before coding, read:
- AGENTS.md
- docs/WEB_UI_CODEX_IMPLEMENTATION_GUIDE.md
- docs/FUNCIONALIDADES_APP.md

The product separates money by person, pocket and currency. CRC and USD must never be mixed automatically.

The Plan baseline is immutable unless explicitly approved. Real transactions are compared against the plan but must not mutate it.

The UI must feel calm, clean, minimal and trustworthy. Avoid visual saturation. AI should be a subtle intelligence layer, not a noisy chatbot.

Work in small, reviewable changes. Do not implement backend unless explicitly asked.
```

### Prompt para revisión de UI

```txt
Review the current Dashboard UI against the HogarClaro design principles.

Check:
- visual saturation
- number of blocks
- hierarchy
- use of color
- AI presence
- clarity of next action
- financial copy
- responsiveness

Suggest and implement minimal changes only.
Do not redesign unrelated components.
```

### Prompt para refactor

```txt
Refactor the current implementation to improve maintainability.

Goals:
- extract repeated UI into reusable components
- move hardcoded financial data into mock data
- move calculations into pure functions
- keep existing visual behavior
- do not introduce backend
- do not change product rules
```

### Prompt para tests

```txt
Add or improve tests for the finance logic.

Focus on business rules, not snapshots:
- currency separation
- pocket separation
- immutable baseline
- plan vs real comparison
- partial payments
- debt avalanche sorting
- spending guardrail status
```

---

## 10. Reglas de calidad

Codex debe respetar estas reglas:

1. No sumar CRC y USD sin conversión explícita.
2. No cruzar bolsillos automáticamente.
3. No modificar el baseline del plan desde transacciones reales.
4. No crear datos financieros hardcodeados dentro de componentes.
5. No crear pantallas saturadas.
6. No usar más colores de los definidos.
7. No poner “IA” en cada tarjeta.
8. No crear backend si la tarea es solo UI.
9. No implementar P2 antes de completar P0.
10. No ocultar trade-offs financieros.
11. Toda recomendación debe explicar razón o impacto.
12. Toda lógica financiera debe tener tests.
13. Toda UI principal debe ser responsive.
14. Todo texto visible debe estar en español.
15. La app debe sentirse calmada, no alarmista.

---

## 11. Definition of Done por pantalla

Una pantalla está lista cuando:

- Responde una pregunta principal.
- Usa componentes del design system.
- Usa datos mock tipados o datos reales controlados.
- Tiene estados loading/empty/error cuando aplique.
- Mantiene monedas y bolsillos separados.
- No tiene números críticos hardcodeados.
- Pasa lint.
- Pasa tests aplicables.
- Es responsive.
- El copy está en español.
- La acción principal es clara.

---

## 12. Siguiente paso recomendado

Pedir a Codex la primera vertical slice:

```txt
Implement V0.1, V0.2 and V0.3 only:
- project setup
- design system
- dashboard static UI

Use mock data but do not implement full financial logic yet.
Follow AGENTS.md and docs/WEB_UI_CODEX_IMPLEMENTATION_GUIDE.md.
```

Criterio de éxito:

> Una persona debe entender en menos de 5 segundos si el hogar está bien este mes, qué pago sigue y cuál es la mejor acción sugerida.
