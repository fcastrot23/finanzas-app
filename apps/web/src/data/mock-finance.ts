import type {
  DashboardMetric,
  Debt,
  HouseholdMember,
  Insight,
  PlannedPayment,
  PlanVsRealPoint,
  Pocket,
  Transaction,
} from "@/types/finance";

export const householdMembers: HouseholdMember[] = [
  {
    id: "fau",
    name: "Fau",
    defaultCurrency: "USD",
  },
  {
    id: "mari",
    name: "Mari",
    defaultCurrency: "CRC",
  },
];

export const pockets: Pocket[] = [
  {
    id: "fau-usd",
    ownerId: "fau",
    currency: "USD",
    name: "Colchón Fau",
    balance: 1275,
  },
  {
    id: "mari-crc",
    ownerId: "mari",
    currency: "CRC",
    name: "Colchón Mari",
    balance: 133575,
  },
];

export const upcomingPayments: PlannedPayment[] = [
  {
    id: "plan-carro-jun",
    date: "2026-06-02",
    concept: "Carro",
    description: "Préstamo Toyota",
    amount: 456,
    currency: "USD",
    pocketId: "fau-usd",
    status: "paid",
  },
  {
    id: "plan-hipoteca-jun",
    date: "2026-06-05",
    concept: "Hipoteca",
    description: "Cuota mensual",
    amount: 275000,
    currency: "CRC",
    pocketId: "mari-crc",
    status: "upcoming",
  },
  {
    id: "plan-escuela-jun",
    date: "2026-06-07",
    concept: "Escuela",
    description: "Mensualidad",
    amount: 95000,
    currency: "CRC",
    pocketId: "mari-crc",
    status: "review",
  },
];

export const realTransactions: Transaction[] = [
  {
    id: "tx-carro-1",
    date: "2026-06-02",
    concept: "Carro",
    amount: 456,
    currency: "USD",
    pocketId: "fau-usd",
    category: "Deuda",
    source: "manual",
    matchedPlanId: "plan-carro-jun",
  },
  {
    id: "tx-ocio-1",
    date: "2026-06-04",
    concept: "Cena familiar",
    amount: 18900,
    currency: "CRC",
    pocketId: "mari-crc",
    category: "Ocio",
    source: "manual",
    outOfPlan: true,
  },
];

export const debts: Debt[] = [
  {
    id: "debt-bac",
    name: "Tarjeta BAC",
    type: "consumer",
    balance: 321134,
    currency: "USD",
    interestRate: 38,
    monthlyPayment: 275,
    priorityRank: 1,
  },
  {
    id: "debt-car",
    name: "Carro",
    type: "secured",
    balance: 18400,
    currency: "USD",
    interestRate: 9.4,
    monthlyPayment: 456,
    priorityRank: 2,
  },
];

export const planVsRealSeries: PlanVsRealPoint[] = [
  { label: "1 jun", plan: 120000, real: 90000, currency: "CRC" },
  { label: "8 jun", plan: 420000, real: 340000, currency: "CRC" },
  { label: "15 jun", plan: 690000, real: 560000, currency: "CRC" },
  { label: "22 jun", plan: 960000, real: 790000, currency: "CRC" },
  { label: "29 jun", plan: 1210000, real: 1080000, currency: "CRC" },
  { label: "30 jun", plan: 1275000, real: 1155000, currency: "CRC" },
];

export const dashboardMetrics: DashboardMetric[] = [
  {
    id: "available-buffer",
    title: "Colchón disponible",
    value: "$1,275 + ₡133,575",
    helper: "Separado por moneda",
    tone: "positive",
  },
  {
    id: "next-payment",
    title: "Próximo pago",
    value: "Carro · 2 jun · $456",
    helper: "Listo para pagar",
    tone: "brand",
  },
  {
    id: "priority-debt",
    title: "Deuda prioritaria",
    value: "Tarjeta BAC · $321,134",
    helper: "Mayor tasa de interés",
    tone: "brand",
  },
  {
    id: "leisure",
    title: "Ocio disponible",
    value: "₡12,100",
    helper: "Para disfrutar sin salirse",
    tone: "positive",
  },
];

export const monthlyPulse = {
  title: "Pulso financiero del mes",
  body: "Vas dentro del plan. Hay 2 decisiones y 1 pago que requieren atención esta semana.",
  chips: ["Dentro del plan", "2 decisiones", "1 alerta"],
};

export const suggestedAction: Insight = {
  title: "Mejor acción sugerida",
  body: "Hacer un abono extra a BAC podría reducir intereses este mes.",
  actionLabel: "Ver recomendación",
  tone: "positive",
};

export const attentionInsight: Insight = {
  title: "Requiere atención",
  body: "Escuela está en revisión. Confirmá el bolsillo antes de marcarla como pagada.",
  actionLabel: "Revisar pago",
  tone: "warning",
};
