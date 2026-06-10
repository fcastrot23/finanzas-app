import type { Debt } from "@/types/finance";

export function sortDebtsByAvalanche(debts: Debt[]) {
  return [...debts]
    .sort((first, second) => {
      const firstRate = first.interestRate ?? -1;
      const secondRate = second.interestRate ?? -1;

      if (secondRate !== firstRate) {
        return secondRate - firstRate;
      }

      return second.balance - first.balance;
    })
    .map((debt, index) => ({
      ...debt,
      priorityRank: index + 1,
    }));
}

export function getPriorityDebt(debts: Debt[]) {
  return sortDebtsByAvalanche(debts)[0] ?? null;
}
