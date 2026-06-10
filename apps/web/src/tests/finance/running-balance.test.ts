import { describe, expect, it } from "vitest";

import { pockets, realTransactions } from "@/data/mock-finance";
import { calculateCurrentBalance } from "@/lib/finance/running-balance";

describe("running balance", () => {
  it("calcula saldo por bolsillo sin cruzar monedas ni propietarios", () => {
    const mariPocket = pockets.find((pocket) => pocket.id === "mari-crc-buffer");

    expect(mariPocket).toBeDefined();
    expect(calculateCurrentBalance(mariPocket!, realTransactions)).toBe(150000);
  });

  it("rechaza transacciones de otra moneda en el mismo bolsillo", () => {
    const fauPocket = pockets.find((pocket) => pocket.id === "fau-usd-buffer");

    expect(fauPocket).toBeDefined();
    expect(() =>
      calculateCurrentBalance(fauPocket!, [
        {
          ...realTransactions[0],
          id: "tx-wrong-currency",
          currency: "CRC",
          pocketId: fauPocket!.id,
        },
      ]),
    ).toThrow("Una transacción no puede afectar un bolsillo de otra moneda.");
  });
});
