import { describe, expect, it } from "vitest";

import { monthlyPlanBaseline, realTransactions } from "@/data/mock-finance";
import {
  calculatePlanVsRealByCurrency,
  detectOutOfPlanTransactions,
  matchTransactionsToPlan,
} from "@/lib/finance/plan-vs-real";

describe("plan vs real", () => {
  it("no muta el baseline aprobado al comparar pagos reales", () => {
    const before = structuredClone(monthlyPlanBaseline);

    matchTransactionsToPlan(monthlyPlanBaseline.items, realTransactions);

    expect(monthlyPlanBaseline).toEqual(before);
  });

  it("permite varios pagos parciales contra una misma línea del plan", () => {
    const matches = matchTransactionsToPlan(
      monthlyPlanBaseline.items,
      realTransactions,
      "2026-06-06",
    );
    const bacMatch = matches.find((match) => match.plan.id === "plan-bac-jun");

    expect(bacMatch?.realPayments).toHaveLength(2);
    expect(bacMatch?.paidAmount).toBe(395);
    expect(bacMatch?.remainingAmount).toBe(155);
    expect(bacMatch?.status).toBe("partial");
  });

  it("marca transacciones no emparejadas como fuera de plan", () => {
    const outOfPlan = detectOutOfPlanTransactions(
      monthlyPlanBaseline.items,
      realTransactions,
    );

    expect(outOfPlan.map((transaction) => transaction.id)).toContain("tx-moose");
  });

  it("compara CRC y USD por separado", () => {
    const crcComparison = calculatePlanVsRealByCurrency(
      monthlyPlanBaseline.items,
      realTransactions,
      "CRC",
    );
    const usdComparison = calculatePlanVsRealByCurrency(
      monthlyPlanBaseline.items,
      realTransactions,
      "USD",
    );

    expect(crcComparison.currency).toBe("CRC");
    expect(usdComparison.currency).toBe("USD");
    expect(crcComparison.plannedAmount).not.toBe(usdComparison.plannedAmount);
  });
});
