import { PlanVsRealChart } from "@/components/dashboard/PlanVsRealChart";
import { FinanceTable } from "@/components/finance/FinanceTable";
import { PageIntro } from "@/components/finance/PageIntro";
import { PageFrame } from "@/components/layout/PageFrame";
import { StatusChip } from "@/components/ui/StatusChip";
import { monthlyPlanBaseline, realTransactions } from "@/data/mock-finance";
import { formatCompactMoney } from "@/lib/finance/currency";
import {
  buildPlanVsRealSeries,
  detectOutOfPlanTransactions,
  matchTransactionsToPlan,
} from "@/lib/finance/plan-vs-real";
import type { PlanMatch } from "@/types/finance";

export default function PlanVsRealPage() {
  const series = buildPlanVsRealSeries(
    monthlyPlanBaseline.items,
    realTransactions,
    "CRC",
  );
  const matches = matchTransactionsToPlan(monthlyPlanBaseline.items, realTransactions);
  const outOfPlan = detectOutOfPlanTransactions(
    monthlyPlanBaseline.items,
    realTransactions,
  );

  return (
    <PageFrame title="Plan vs Real">
      <div className="space-y-6">
      <PageIntro
        body="Las transacciones reales se emparejan contra el baseline sin cambiar el plan original."
        title="¿Qué se desvió del plan?"
      />
      <PlanVsRealChart data={series} />
      <FinanceTable<PlanMatch>
        columns={[
          {
            key: "concept",
            label: "Línea del plan",
            render: (row) => row.plan.concept,
          },
          {
            key: "planned",
            label: "Plan",
            align: "right",
            render: (row) => formatCompactMoney(row.plan.amount, row.plan.currency),
          },
          {
            key: "real",
            label: "Real emparejado",
            align: "right",
            render: (row) => formatCompactMoney(row.paidAmount, row.plan.currency),
          },
          {
            key: "remaining",
            label: "Pendiente",
            align: "right",
            render: (row) =>
              formatCompactMoney(row.remainingAmount, row.plan.currency),
          },
          {
            key: "matches",
            label: "Pagos",
            render: (row) => `${row.realPayments.length}`,
          },
        ]}
        getRowKey={(row) => row.plan.id}
        rows={matches}
      />
      <div className="rounded-card border border-border bg-surface p-5 shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-primary">Fuera de plan</h2>
            <p className="mt-1 text-sm text-secondary">
              Se revisa al cierre para decidir si entra al siguiente baseline.
            </p>
          </div>
          <StatusChip tone={outOfPlan.length > 0 ? "warning" : "positive"}>
            {outOfPlan.length} movimiento
          </StatusChip>
        </div>
      </div>
      </div>
    </PageFrame>
  );
}
