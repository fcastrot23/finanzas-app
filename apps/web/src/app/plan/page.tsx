import { FinanceTable } from "@/components/finance/FinanceTable";
import { PageIntro } from "@/components/finance/PageIntro";
import { PageFrame } from "@/components/layout/PageFrame";
import { StatusChip } from "@/components/ui/StatusChip";
import { monthlyPlanBaseline, realTransactions } from "@/data/mock-finance";
import { formatCompactMoney } from "@/lib/finance/currency";
import { matchTransactionsToPlan } from "@/lib/finance/plan-vs-real";
import type { PlanMatch } from "@/types/finance";

const statusLabel = {
  paid: "Pagado",
  partial: "Parcial",
  pending: "Pendiente",
  review: "Revisar",
  overdue: "Atrasado",
};

const statusTone = {
  paid: "positive",
  partial: "warning",
  pending: "brand",
  review: "warning",
  overdue: "risk",
} as const;

export default function PlanPage() {
  const matches = matchTransactionsToPlan(monthlyPlanBaseline.items, realTransactions);

  return (
    <PageFrame title="Plan de pagos">
      <div className="space-y-6">
      <PageIntro
        body="El baseline aprobado se usa como vara de comparación. Registrar pagos reales no lo modifica."
        title="¿Qué debo pagar, cuándo y desde qué bolsillo?"
      />
      <FinanceTable<PlanMatch>
        columns={[
          {
            key: "date",
            label: "Fecha",
            render: (row) => row.plan.date,
          },
          {
            key: "concept",
            label: "Pago",
            render: (row) => (
              <div>
                <p className="font-semibold">{row.plan.concept}</p>
                <p className="text-secondary">{row.plan.description}</p>
              </div>
            ),
          },
          {
            key: "amount",
            label: "Plan",
            align: "right",
            render: (row) => formatCompactMoney(row.plan.amount, row.plan.currency),
          },
          {
            key: "paid",
            label: "Real",
            align: "right",
            render: (row) => formatCompactMoney(row.paidAmount, row.plan.currency),
          },
          {
            key: "status",
            label: "Estado",
            render: (row) => (
              <StatusChip tone={statusTone[row.status]}>
                {statusLabel[row.status]}
              </StatusChip>
            ),
          },
        ]}
        getRowKey={(row) => row.plan.id}
        rows={matches}
      />
      </div>
    </PageFrame>
  );
}
