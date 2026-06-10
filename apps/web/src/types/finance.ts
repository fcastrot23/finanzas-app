export type Currency = "CRC" | "USD";

export type EntityId = string;

export type HouseholdMember = {
  id: EntityId;
  name: string;
  defaultCurrency: Currency;
};

export type PocketOwnerType = "member" | "household";

export type Pocket = {
  id: EntityId;
  ownerId: EntityId;
  ownerType: PocketOwnerType;
  currency: Currency;
  name: string;
  purpose: "income" | "buffer" | "bills" | "leisure" | "debt" | "emergency";
  startingBalance: number;
  balance: number;
};

export type PaymentStatus = "planned" | "paid" | "upcoming" | "review" | "overdue";

export type PaymentFrequency = "one_time" | "monthly";

export type PlannedPayment = {
  id: EntityId;
  date: string;
  concept: string;
  description: string;
  amount: number;
  currency: Currency;
  pocketId: EntityId;
  category: string;
  frequency: PaymentFrequency;
  status: PaymentStatus;
};

export type PlanBaseline = {
  id: EntityId;
  name: string;
  month: string;
  approvedAt: string;
  approvedBy: EntityId[];
  items: PlannedPayment[];
};

export type TransactionDirection =
  | "income"
  | "expense"
  | "transfer_in"
  | "transfer_out";

export type Transaction = {
  id: EntityId;
  date: string;
  concept: string;
  amount: number;
  currency: Currency;
  pocketId: EntityId;
  category: string;
  source: "manual" | "imported";
  direction: TransactionDirection;
  paidById: EntityId;
  matchedPlanId?: EntityId;
  outOfPlan?: boolean;
  note?: string;
};

export type Debt = {
  id: EntityId;
  name: string;
  type: "consumer" | "secured";
  balance: number;
  currency: Currency;
  interestRate?: number;
  monthlyPayment: number;
  pocketId: EntityId;
  priorityRank?: number;
};

export type LeisureBudget = {
  id: EntityId;
  name: string;
  ownerId: EntityId;
  pocketId: EntityId;
  currency: Currency;
  monthlyLimit: number;
  spent: number;
  shared: boolean;
};

export type PlanVsRealPoint = {
  label: string;
  plan: number;
  real: number;
  currency: Currency;
};

export type DashboardMetric = {
  id: EntityId;
  title: string;
  value: string;
  helper: string;
  tone: "positive" | "brand" | "warning" | "risk";
};

export type Insight = {
  title: string;
  body: string;
  actionLabel?: string;
  tone: "positive" | "warning" | "risk";
};

export type PlanMatchStatus = "paid" | "partial" | "pending" | "review" | "overdue";

export type PlanMatch = {
  plan: PlannedPayment;
  realPayments: Transaction[];
  paidAmount: number;
  remainingAmount: number;
  status: PlanMatchStatus;
};

export type PocketRunningBalance = {
  pocketId: EntityId;
  currency: Currency;
  rows: {
    transactionId: EntityId;
    date: string;
    concept: string;
    amount: number;
    balance: number;
  }[];
};

export type SpendingGuardrailTone = "green" | "amber" | "red";

export type SpendingGuardrailInput = {
  amount: number;
  currency: Currency;
  concept: string;
  pocketId: EntityId;
  paidById: EntityId;
  shared: boolean;
};

export type SpendingGuardrailResult = {
  tone: SpendingGuardrailTone;
  title: string;
  remainingCushion: number;
  sacrificed: string;
  requiresApproval: boolean;
  currency: Currency;
};
