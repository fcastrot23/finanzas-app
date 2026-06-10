import { FinanceTable } from "@/components/finance/FinanceTable";
import { PageIntro } from "@/components/finance/PageIntro";
import { PageFrame } from "@/components/layout/PageFrame";
import { StatusChip } from "@/components/ui/StatusChip";
import { monthlyPlanBaseline, pockets, realTransactions } from "@/data/mock-finance";
import { formatCompactMoney } from "@/lib/finance/currency";
import { detectOutOfPlanTransactions } from "@/lib/finance/plan-vs-real";
import type { Transaction } from "@/types/finance";

export default function TransactionsPage() {
  const outOfPlan = new Set(
    detectOutOfPlanTransactions(monthlyPlanBaseline.items, realTransactions).map(
      (transaction) => transaction.id,
    ),
  );

  const pocketNameById = new Map(pockets.map((pocket) => [pocket.id, pocket.name]));

  return (
    <PageFrame title="Transacciones">
      <div className="space-y-6">
      <PageIntro
        body="El Real registra pagos efectivos. Puede emparejarse al plan o quedar marcado para revisión."
        title="¿Qué pasó de verdad este mes?"
      />
      <FinanceTable<Transaction>
        columns={[
          { key: "date", label: "Fecha", render: (row) => row.date },
          {
            key: "concept",
            label: "Movimiento",
            render: (row) => (
              <div>
                <p className="font-semibold">{row.concept}</p>
                <p className="text-secondary">{row.category}</p>
              </div>
            ),
          },
          {
            key: "amount",
            label: "Monto",
            align: "right",
            render: (row) => formatCompactMoney(row.amount, row.currency),
          },
          {
            key: "pocket",
            label: "Bolsillo",
            render: (row) => pocketNameById.get(row.pocketId) ?? "Sin bolsillo",
          },
          {
            key: "status",
            label: "Estado",
            render: (row) => (
              <StatusChip tone={outOfPlan.has(row.id) ? "warning" : "positive"}>
                {outOfPlan.has(row.id) ? "Fuera de plan" : "Emparejado"}
              </StatusChip>
            ),
          },
        ]}
        getRowKey={(row) => row.id}
        rows={realTransactions}
      />
      </div>
    </PageFrame>
  );
}
