import { describe, expect, it } from "vitest";

import {
  assertSingleCurrency,
  getPlanVsRealDelta,
} from "@/lib/finance/dashboard-summary";
import type { PlanVsRealPoint } from "@/types/finance";

const crcSeries: PlanVsRealPoint[] = [
  { label: "1 jun", plan: 100000, real: 90000, currency: "CRC" },
  { label: "8 jun", plan: 180000, real: 150000, currency: "CRC" },
];

describe("dashboard summary finance helpers", () => {
  it("calcula desviación sin mutar ni convertir moneda", () => {
    expect(getPlanVsRealDelta(crcSeries)).toEqual({
      amount: 30000,
      currency: "CRC",
    });
  });

  it("rechaza series que mezclan CRC y USD", () => {
    expect(() =>
      assertSingleCurrency([
        ...crcSeries,
        { label: "15 jun", plan: 300, real: 250, currency: "USD" },
      ]),
    ).toThrow("Plan vs Real no puede mezclar CRC y USD automáticamente.");
  });
});
