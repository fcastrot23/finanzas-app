import { describe, expect, it } from "vitest";

import {
  leisureBudgets,
  monthlyPlanBaseline,
  pockets,
  realTransactions,
} from "@/data/mock-finance";
import { evaluateSpendingGuardrail } from "@/lib/finance/spending-guardrail";

const context = {
  pockets,
  leisureBudgets,
  plannedPayments: monthlyPlanBaseline.items,
  transactions: realTransactions,
};

describe("spending guardrail", () => {
  it("devuelve verde si el gasto cabe en el colchón del mes", () => {
    const result = evaluateSpendingGuardrail(
      {
        amount: 5000,
        currency: "CRC",
        concept: "Café",
        pocketId: "hogar-crc-leisure",
        paidById: "fau",
        shared: true,
      },
      context,
    );

    expect(result.tone).toBe("green");
    expect(result.requiresApproval).toBe(false);
  });

  it("devuelve rojo si obliga a atrasar un pago del plan", () => {
    const result = evaluateSpendingGuardrail(
      {
        amount: 200000,
        currency: "CRC",
        concept: "Compra grande",
        pocketId: "mari-crc-buffer",
        paidById: "mari",
        shared: true,
      },
      context,
    );

    expect(result.tone).toBe("red");
    expect(result.requiresApproval).toBe(true);
  });

  it("devuelve ámbar si toca emergencia pero no atrasa el plan", () => {
    const result = evaluateSpendingGuardrail(
      {
        amount: 25000,
        currency: "CRC",
        concept: "Día familiar",
        pocketId: "hogar-crc-leisure",
        paidById: "fau",
        shared: true,
      },
      context,
    );

    expect(result.tone).toBe("amber");
    expect(result.requiresApproval).toBe(true);
  });

  it("rechaza evaluar contra un bolsillo de otra moneda", () => {
    expect(() =>
      evaluateSpendingGuardrail(
        {
          amount: 100,
          currency: "USD",
          concept: "Error",
          pocketId: "hogar-crc-leisure",
          paidById: "fau",
          shared: false,
        },
        context,
      ),
    ).toThrow("El gasto no puede evaluarse contra un bolsillo de otra moneda.");
  });
});
