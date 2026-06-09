import type { Currency, PlannedPayment, PlanVsRealPoint } from "@/types/finance";

export function assertSingleCurrency(points: PlanVsRealPoint[]): Currency | null {
  const currencies = new Set(points.map((point) => point.currency));

  if (currencies.size > 1) {
    throw new Error("Plan vs Real no puede mezclar CRC y USD automáticamente.");
  }

  return points[0]?.currency ?? null;
}

export function getPlanVsRealDelta(points: PlanVsRealPoint[]) {
  const currency = assertSingleCurrency(points);
  const lastPoint = points.at(-1);

  return {
    currency,
    amount: lastPoint ? lastPoint.plan - lastPoint.real : 0,
  };
}

export function getNextPayment(payments: PlannedPayment[]) {
  return payments.find((payment) => payment.status !== "paid") ?? payments[0] ?? null;
}
