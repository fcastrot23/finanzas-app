import type { Pocket, PocketRunningBalance, Transaction } from "@/types/finance";

function transactionImpact(transaction: Transaction) {
  if (transaction.direction === "income" || transaction.direction === "transfer_in") {
    return transaction.amount;
  }

  return -transaction.amount;
}

export function calculateRunningBalanceByPocket(
  pocket: Pocket,
  transactions: Transaction[],
): PocketRunningBalance {
  const pocketTransactions = transactions
    .filter((transaction) => transaction.pocketId === pocket.id)
    .sort((first, second) => first.date.localeCompare(second.date));

  let balance = pocket.startingBalance;

  return {
    pocketId: pocket.id,
    currency: pocket.currency,
    rows: pocketTransactions.map((transaction) => {
      if (transaction.currency !== pocket.currency) {
        throw new Error("Una transacción no puede afectar un bolsillo de otra moneda.");
      }

      balance += transactionImpact(transaction);

      return {
        transactionId: transaction.id,
        date: transaction.date,
        concept: transaction.concept,
        amount: transactionImpact(transaction),
        balance,
      };
    }),
  };
}

export function calculateCurrentBalance(pocket: Pocket, transactions: Transaction[]) {
  const runningBalance = calculateRunningBalanceByPocket(pocket, transactions);
  const lastRow = runningBalance.rows.at(-1);

  return lastRow?.balance ?? pocket.startingBalance;
}
