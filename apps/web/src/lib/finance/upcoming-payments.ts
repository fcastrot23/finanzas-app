import type { PaymentStatus, PlannedPayment, Transaction } from "@/types/finance";

export function getUpcomingPaymentStatus(
  payment: PlannedPayment,
  transactions: Transaction[],
  asOfDate: string,
): PaymentStatus {
  if (payment.status === "review") {
    return "review";
  }

  const paidAmount = transactions
    .filter((transaction) => transaction.matchedPlanId === payment.id)
    .reduce((total, transaction) => total + transaction.amount, 0);

  if (paidAmount >= payment.amount) {
    return "paid";
  }

  if (payment.date < asOfDate) {
    return "overdue";
  }

  return "upcoming";
}

export function getNextPayment(payments: PlannedPayment[], asOfDate = "2026-06-10") {
  return (
    [...payments]
      .sort((first, second) => first.date.localeCompare(second.date))
      .find((payment) => payment.status !== "paid" && payment.date >= asOfDate) ??
    payments.find((payment) => payment.status !== "paid") ??
    null
  );
}

export function getUpcomingPayments(payments: PlannedPayment[], limit = 4) {
  return [...payments]
    .sort((first, second) => first.date.localeCompare(second.date))
    .slice(0, limit);
}
