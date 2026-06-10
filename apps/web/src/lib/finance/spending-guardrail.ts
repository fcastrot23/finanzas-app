import type {
  LeisureBudget,
  Pocket,
  PlannedPayment,
  SpendingGuardrailInput,
  SpendingGuardrailResult,
  Transaction,
} from "@/types/finance";

type SpendingGuardrailContext = {
  pockets: Pocket[];
  leisureBudgets: LeisureBudget[];
  plannedPayments: PlannedPayment[];
  transactions: Transaction[];
};

export function evaluateSpendingGuardrail(
  input: SpendingGuardrailInput,
  context: SpendingGuardrailContext,
): SpendingGuardrailResult {
  const pocket = context.pockets.find((candidate) => candidate.id === input.pocketId);

  if (!pocket) {
    throw new Error("El bolsillo seleccionado no existe.");
  }

  if (pocket.currency !== input.currency) {
    throw new Error("El gasto no puede evaluarse contra un bolsillo de otra moneda.");
  }

  const leisureBudget = context.leisureBudgets.find(
    (budget) => budget.pocketId === input.pocketId && budget.currency === input.currency,
  );
  const availableLeisure = leisureBudget
    ? leisureBudget.monthlyLimit - leisureBudget.spent
    : pocket.balance;

  if (leisureBudget && input.amount <= availableLeisure) {
    return {
      tone: "green",
      title: "Cabe en tu colchón del mes",
      remainingCushion: availableLeisure - input.amount,
      sacrificed: "No sacrifica pagos del plan.",
      requiresApproval: false,
      currency: input.currency,
    };
  }

  const emergencyAvailable = context.pockets
    .filter(
      (candidate) =>
        candidate.currency === input.currency && candidate.purpose === "emergency",
    )
    .reduce((total, candidate) => total + candidate.balance, 0);

  if (leisureBudget && input.amount <= availableLeisure + emergencyAvailable) {
    return {
      tone: "amber",
      title: "Toca tu fondo de emergencia",
      remainingCushion: availableLeisure - input.amount,
      sacrificed: "Reduce margen para ocio o imprevistos.",
      requiresApproval: input.shared,
      currency: input.currency,
    };
  }

  if (leisureBudget) {
    return {
      tone: "red",
      title: "Obliga a atrasar un pago del plan",
      remainingCushion: availableLeisure - input.amount,
      sacrificed: "Tendrías que mover o atrasar un pago pendiente.",
      requiresApproval: true,
      currency: input.currency,
    };
  }

  const plannedLeft = context.plannedPayments
    .filter(
      (payment) =>
        payment.pocketId === input.pocketId &&
        payment.currency === input.currency &&
        payment.status !== "paid",
    )
    .reduce((total, payment) => total + payment.amount, 0);
  const remainingCushion = pocket.balance - plannedLeft - input.amount;

  if (input.amount <= availableLeisure && remainingCushion >= 0) {
    return {
      tone: "green",
      title: "Cabe en tu colchón del mes",
      remainingCushion,
      sacrificed: "No sacrifica pagos del plan.",
      requiresApproval: false,
      currency: input.currency,
    };
  }

  if (remainingCushion >= 0) {
    return {
      tone: "amber",
      title: "Toca tu fondo de emergencia",
      remainingCushion,
      sacrificed: "Reduce margen para ocio o imprevistos.",
      requiresApproval: input.shared,
      currency: input.currency,
    };
  }

  return {
    tone: "red",
    title: "Obliga a atrasar un pago del plan",
    remainingCushion,
    sacrificed: "Tendrías que mover o atrasar un pago pendiente.",
    requiresApproval: true,
    currency: input.currency,
  };
}
