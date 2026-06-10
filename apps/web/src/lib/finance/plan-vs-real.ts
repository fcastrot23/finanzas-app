import type {
  Currency,
  PlanMatch,
  PlanMatchStatus,
  PlannedPayment,
  PlanVsRealPoint,
  Transaction,
} from "@/types/finance";

function assertMatchingMoney(plan: PlannedPayment, transaction: Transaction) {
  if (plan.currency !== transaction.currency) {
    throw new Error("No se puede emparejar una transacción de otra moneda.");
  }

  if (plan.pocketId !== transaction.pocketId) {
    throw new Error("No se puede emparejar una transacción de otro bolsillo.");
  }
}

function resolveMatchStatus(
  plan: PlannedPayment,
  paidAmount: number,
  asOfDate: string,
): PlanMatchStatus {
  if (plan.status === "review") {
    return "review";
  }

  if (paidAmount >= plan.amount) {
    return "paid";
  }

  if (paidAmount > 0) {
    return "partial";
  }

  if (plan.date < asOfDate) {
    return "overdue";
  }

  return "pending";
}

export function matchTransactionsToPlan(
  plannedPayments: PlannedPayment[],
  transactions: Transaction[],
  asOfDate = "2026-06-10",
): PlanMatch[] {
  return plannedPayments.map((plan) => {
    const realPayments = transactions.filter(
      (transaction) => transaction.matchedPlanId === plan.id,
    );

    realPayments.forEach((transaction) => assertMatchingMoney(plan, transaction));

    const paidAmount = realPayments.reduce(
      (total, transaction) => total + transaction.amount,
      0,
    );
    const remainingAmount = Math.max(plan.amount - paidAmount, 0);

    return {
      plan,
      realPayments,
      paidAmount,
      remainingAmount,
      status: resolveMatchStatus(plan, paidAmount, asOfDate),
    };
  });
}

export function detectOutOfPlanTransactions(
  plannedPayments: PlannedPayment[],
  transactions: Transaction[],
) {
  const planIds = new Set(plannedPayments.map((payment) => payment.id));

  return transactions.filter(
    (transaction) =>
      transaction.outOfPlan ||
      !transaction.matchedPlanId ||
      !planIds.has(transaction.matchedPlanId),
  );
}

export function calculatePlanVsRealByCurrency(
  plannedPayments: PlannedPayment[],
  transactions: Transaction[],
  currency: Currency,
) {
  const plannedAmount = plannedPayments
    .filter((payment) => payment.currency === currency)
    .reduce((total, payment) => total + payment.amount, 0);
  const realAmount = transactions
    .filter((transaction) => transaction.currency === currency && !transaction.outOfPlan)
    .reduce((total, transaction) => total + transaction.amount, 0);

  return {
    currency,
    plannedAmount,
    realAmount,
    delta: plannedAmount - realAmount,
  };
}

export function buildPlanVsRealSeries(
  plannedPayments: PlannedPayment[],
  transactions: Transaction[],
  currency: Currency,
): PlanVsRealPoint[] {
  const dates = Array.from(
    new Set([
      ...plannedPayments
        .filter((payment) => payment.currency === currency)
        .map((payment) => payment.date),
      ...transactions
        .filter((transaction) => transaction.currency === currency)
        .map((transaction) => transaction.date),
    ]),
  ).sort();

  let plan = 0;
  let real = 0;

  return dates.map((date) => {
    plan += plannedPayments
      .filter((payment) => payment.currency === currency && payment.date === date)
      .reduce((total, payment) => total + payment.amount, 0);
    real += transactions
      .filter(
        (transaction) =>
          transaction.currency === currency &&
          transaction.date === date &&
          !transaction.outOfPlan,
      )
      .reduce((total, transaction) => total + transaction.amount, 0);

    return {
      label: new Intl.DateTimeFormat("es-CR", {
        day: "numeric",
        month: "short",
        timeZone: "UTC",
      })
        .format(new Date(date))
        .replace(".", ""),
      plan,
      real,
      currency,
    };
  });
}
