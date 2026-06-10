import { FinanceTable } from "@/components/finance/FinanceTable";
import { PageIntro } from "@/components/finance/PageIntro";
import { PageFrame } from "@/components/layout/PageFrame";
import { StatusChip } from "@/components/ui/StatusChip";
import { debts } from "@/data/mock-finance";
import { formatCompactMoney } from "@/lib/finance/currency";
import type { Debt } from "@/types/finance";

export default function DebtsPage() {
  return (
    <PageFrame title="Deudas">
      <div className="space-y-6">
      <PageIntro
        body="La estrategia avalancha prioriza la tasa más alta. Las deudas sin tasa quedan después."
        title="¿Qué deuda debo atacar primero?"
      />
      <FinanceTable<Debt>
        columns={[
          {
            key: "rank",
            label: "Prioridad",
            render: (row) => (
              <StatusChip tone={row.priorityRank === 1 ? "warning" : "brand"}>
                {row.priorityRank}
              </StatusChip>
            ),
          },
          {
            key: "name",
            label: "Deuda",
            render: (row) => row.name,
          },
          {
            key: "rate",
            label: "Tasa",
            align: "right",
            render: (row) =>
              row.interestRate ? `${row.interestRate.toFixed(1)}%` : "Sin tasa",
          },
          {
            key: "balance",
            label: "Saldo",
            align: "right",
            render: (row) => formatCompactMoney(row.balance, row.currency),
          },
          {
            key: "payment",
            label: "Cuota",
            align: "right",
            render: (row) => formatCompactMoney(row.monthlyPayment, row.currency),
          },
        ]}
        getRowKey={(row) => row.id}
        rows={debts}
      />
      </div>
    </PageFrame>
  );
}
