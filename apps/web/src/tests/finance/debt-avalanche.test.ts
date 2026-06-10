import { describe, expect, it } from "vitest";

import { sortDebtsByAvalanche } from "@/lib/finance/debt-avalanche";
import type { Debt } from "@/types/finance";

const debts: Debt[] = [
  {
    id: "no-rate",
    name: "Sin tasa",
    type: "consumer",
    balance: 1000,
    currency: "USD",
    monthlyPayment: 50,
    pocketId: "hogar-usd-debt",
  },
  {
    id: "high-rate",
    name: "Alta tasa",
    type: "consumer",
    balance: 500,
    currency: "USD",
    interestRate: 35,
    monthlyPayment: 60,
    pocketId: "hogar-usd-debt",
  },
  {
    id: "low-rate",
    name: "Baja tasa",
    type: "secured",
    balance: 2000,
    currency: "USD",
    interestRate: 8,
    monthlyPayment: 100,
    pocketId: "fau-usd-buffer",
  },
];

describe("debt avalanche", () => {
  it("ordena por tasa y deja deudas sin tasa al final", () => {
    const sorted = sortDebtsByAvalanche(debts);

    expect(sorted.map((debt) => debt.id)).toEqual([
      "high-rate",
      "low-rate",
      "no-rate",
    ]);
    expect(sorted[0].priorityRank).toBe(1);
  });
});
