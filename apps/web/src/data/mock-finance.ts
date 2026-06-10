import { sortDebtsByAvalanche } from "@/lib/finance/debt-avalanche";
import { formatCompactMoney } from "@/lib/finance/currency";
import { getNextPayment } from "@/lib/finance/upcoming-payments";
import type {
  DashboardMetric,
  Debt,
  HouseholdMember,
  Insight,
  LeisureBudget,
  PlanBaseline,
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
    id: "fau-usd-buffer",
    ownerId: "fau",
    ownerType: "member",
    currency: "USD",
    name: "Colchón Fau",
    purpose: "buffer",
    startingBalance: 2200,
    balance: 1275,
  },
  {
    id: "fau-crc-bills",
    ownerId: "fau",
    ownerType: "member",
    currency: "CRC",
    name: "Pagos Fau CRC",
    purpose: "bills",
    startingBalance: 155000,
    balance: 74200,
  },
  {
    id: "mari-crc-buffer",
    ownerId: "mari",
    ownerType: "member",
    currency: "CRC",
    name: "Colchón Mari",
    purpose: "buffer",
    startingBalance: 425000,
    balance: 133575,
  },
  {
    id: "hogar-crc-leisure",
    ownerId: "hogar",
    ownerType: "household",
    currency: "CRC",
    name: "Ocio hogar",
    purpose: "leisure",
    startingBalance: 65000,
    balance: 12100,
  },
  {
    id: "hogar-usd-debt",
    ownerId: "hogar",
    ownerType: "household",
    currency: "USD",
    name: "Deudas USD",
    purpose: "debt",
    startingBalance: 900,
    balance: 265,
  },
  {
    id: "hogar-crc-emergency",
    ownerId: "hogar",
    ownerType: "household",
    currency: "CRC",
    name: "Emergencia CRC",
    purpose: "emergency",
    startingBalance: 250000,
    balance: 250000,
  },
];

export const monthlyPlanBaseline: PlanBaseline = {
  id: "baseline-2026-06",
  name: "Plan aprobado junio",
  month: "2026-06",
  approvedAt: "2026-05-30T18:00:00-06:00",
  approvedBy: ["fau", "mari"],
  items: [
    {
      id: "plan-carro-jun",
      date: "2026-06-02",
      concept: "Carro",
      description: "Préstamo Toyota",
      amount: 456,
      currency: "USD",
      pocketId: "fau-usd-buffer",
      category: "Deuda",
      frequency: "monthly",
      status: "paid",
    },
    {
      id: "plan-bac-jun",
      date: "2026-06-04",
      concept: "Tarjeta BAC",
      description: "Pago mínimo y abono avalancha",
      amount: 550,
      currency: "USD",
      pocketId: "hogar-usd-debt",
      category: "Deuda",
      frequency: "monthly",
      status: "planned",
    },
    {
      id: "plan-hipoteca-jun",
      date: "2026-06-05",
      concept: "Hipoteca",
      description: "Cuota mensual",
      amount: 275000,
      currency: "CRC",
      pocketId: "mari-crc-buffer",
      category: "Casa",
      frequency: "monthly",
      status: "upcoming",
    },
    {
      id: "plan-escuela-jun",
      date: "2026-06-07",
      concept: "Escuela",
      description: "Mensualidad",
      amount: 95000,
      currency: "CRC",
      pocketId: "mari-crc-buffer",
      category: "Familia",
      frequency: "monthly",
      status: "review",
    },
    {
      id: "plan-ocio-jun",
      date: "2026-06-12",
      concept: "Ocio hogar",
      description: "Salidas y gustos compartidos",
      amount: 65000,
      currency: "CRC",
      pocketId: "hogar-crc-leisure",
      category: "Ocio",
      frequency: "monthly",
      status: "planned",
    },
    {
      id: "plan-servicios-jun",
      date: "2026-06-14",
      concept: "Servicios",
      description: "Agua, luz e internet",
      amount: 80500,
      currency: "CRC",
      pocketId: "fau-crc-bills",
      category: "Casa",
      frequency: "monthly",
      status: "planned",
    },
  ],
};

export const realTransactions: Transaction[] = [
  {
    id: "tx-carro-1",
    date: "2026-06-02",
    concept: "Carro",
    amount: 456,
    currency: "USD",
    pocketId: "fau-usd-buffer",
    category: "Deuda",
    source: "manual",
    direction: "expense",
    paidById: "fau",
    matchedPlanId: "plan-carro-jun",
  },
  {
    id: "tx-bac-1",
    date: "2026-06-03",
    concept: "Tarjeta BAC",
    amount: 275,
    currency: "USD",
    pocketId: "hogar-usd-debt",
    category: "Deuda",
    source: "manual",
    direction: "expense",
    paidById: "fau",
    matchedPlanId: "plan-bac-jun",
  },
  {
    id: "tx-bac-2",
    date: "2026-06-06",
    concept: "Abono BAC",
    amount: 120,
    currency: "USD",
    pocketId: "hogar-usd-debt",
    category: "Deuda",
    source: "manual",
    direction: "expense",
    paidById: "mari",
    matchedPlanId: "plan-bac-jun",
  },
  {
    id: "tx-hipoteca-1",
    date: "2026-06-05",
    concept: "Hipoteca",
    amount: 275000,
    currency: "CRC",
    pocketId: "mari-crc-buffer",
    category: "Casa",
    source: "manual",
    direction: "expense",
    paidById: "mari",
    matchedPlanId: "plan-hipoteca-jun",
  },
  {
    id: "tx-ocio-1",
    date: "2026-06-04",
    concept: "Cena familiar",
    amount: 18900,
    currency: "CRC",
    pocketId: "hogar-crc-leisure",
    category: "Ocio",
    source: "manual",
    direction: "expense",
    paidById: "mari",
    matchedPlanId: "plan-ocio-jun",
  },
  {
    id: "tx-moose",
    date: "2026-06-08",
    concept: "Moose",
    amount: 34000,
    currency: "CRC",
    pocketId: "hogar-crc-leisure",
    category: "Ocio",
    source: "manual",
    direction: "expense",
    paidById: "fau",
    outOfPlan: true,
    note: "Gasto fuera de plan para revisar al cierre.",
  },
];

export const debts: Debt[] = sortDebtsByAvalanche([
  {
    id: "debt-bac",
    name: "Tarjeta BAC",
    type: "consumer",
    balance: 321134,
    currency: "USD",
    interestRate: 38,
    monthlyPayment: 275,
    pocketId: "hogar-usd-debt",
  },
  {
    id: "debt-car",
    name: "Carro",
    type: "secured",
    balance: 18400,
    currency: "USD",
    interestRate: 9.4,
    monthlyPayment: 456,
    pocketId: "fau-usd-buffer",
  },
  {
    id: "debt-family",
    name: "Préstamo familiar",
    type: "consumer",
    balance: 450000,
    currency: "CRC",
    monthlyPayment: 50000,
    pocketId: "mari-crc-buffer",
  },
]);

export const leisureBudgets: LeisureBudget[] = [
  {
    id: "leisure-household-crc",
    name: "Ocio hogar",
    ownerId: "hogar",
    pocketId: "hogar-crc-leisure",
    currency: "CRC",
    monthlyLimit: 65000,
    spent: 52900,
    shared: true,
  },
  {
    id: "leisure-fau-usd",
    name: "Gustos Fau",
    ownerId: "fau",
    pocketId: "fau-usd-buffer",
    currency: "USD",
    monthlyLimit: 120,
    spent: 45,
    shared: false,
  },
];

export const upcomingPayments = monthlyPlanBaseline.items.slice(0, 4);

export const planVsRealSeries: PlanVsRealPoint[] = [
  { label: "1 jun", plan: 120000, real: 90000, currency: "CRC" },
  { label: "8 jun", plan: 420000, real: 340000, currency: "CRC" },
  { label: "15 jun", plan: 690000, real: 560000, currency: "CRC" },
  { label: "22 jun", plan: 960000, real: 790000, currency: "CRC" },
  { label: "29 jun", plan: 1210000, real: 1080000, currency: "CRC" },
  { label: "30 jun", plan: 1275000, real: 1155000, currency: "CRC" },
];

const nextPayment = getNextPayment(monthlyPlanBaseline.items, "2026-06-03");
const priorityDebt = debts[0];
const householdLeisure = leisureBudgets[0];

export const dashboardMetrics: DashboardMetric[] = [
  {
    id: "available-buffer",
    title: "Colchón disponible",
    value: `${formatCompactMoney(1275, "USD")} + ${formatCompactMoney(133575, "CRC")}`,
    helper: "Separado por moneda",
    tone: "positive",
  },
  {
    id: "next-payment",
    title: "Próximo pago",
    value: nextPayment
      ? `${nextPayment.concept} · ${formatCompactMoney(nextPayment.amount, nextPayment.currency)}`
      : "Sin pagos pendientes",
    helper: nextPayment ? "Listo para revisar" : "Todo al día",
    tone: "brand",
  },
  {
    id: "priority-debt",
    title: "Deuda prioritaria",
    value: priorityDebt
      ? `${priorityDebt.name} · ${formatCompactMoney(priorityDebt.balance, priorityDebt.currency)}`
      : "Sin deuda prioritaria",
    helper: "Mayor tasa de interés",
    tone: "brand",
  },
  {
    id: "leisure",
    title: "Ocio disponible",
    value: formatCompactMoney(
      householdLeisure.monthlyLimit - householdLeisure.spent,
      householdLeisure.currency,
    ),
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
