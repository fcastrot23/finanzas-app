export type Currency = "CRC" | "USD";

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

export type PaymentStatus = "paid" | "upcoming" | "review" | "overdue";

export type PlannedPayment = {
  id: string;
  date: string;
  concept: string;
  description: string;
  amount: number;
  currency: Currency;
  pocketId: string;
  status: PaymentStatus;
};

export type Transaction = {
  id: string;
  date: string;
  concept: string;
  amount: number;
  currency: Currency;
  pocketId: string;
  category: string;
  source: "manual" | "imported";
  matchedPlanId?: string;
  outOfPlan?: boolean;
};

export type Debt = {
  id: string;
  name: string;
  type: "consumer" | "secured";
  balance: number;
  currency: Currency;
  interestRate?: number;
  monthlyPayment: number;
  priorityRank?: number;
};

export type PlanVsRealPoint = {
  label: string;
  plan: number;
  real: number;
  currency: Currency;
};

export type DashboardMetric = {
  id: string;
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
