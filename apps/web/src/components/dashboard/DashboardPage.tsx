import { FinancialPulse } from "@/components/dashboard/FinancialPulse";
import { InsightCard } from "@/components/dashboard/InsightCard";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { PlanVsRealChart } from "@/components/dashboard/PlanVsRealChart";
import { UpcomingPayments } from "@/components/dashboard/UpcomingPayments";
import { SpendingGuardrailModal } from "@/components/finance/SpendingGuardrailModal";
import { AppShell } from "@/components/layout/AppShell";
import { TopBar } from "@/components/layout/TopBar";
import {
  attentionInsight,
  dashboardMetrics,
  householdMembers,
  monthlyPulse,
  planVsRealSeries,
  suggestedAction,
  upcomingPayments,
} from "@/data/mock-finance";

export function DashboardPage() {
  return (
    <AppShell>
      <TopBar action={<SpendingGuardrailModal />} members={householdMembers} />

      <div className="space-y-6">
        <FinancialPulse
          body={monthlyPulse.body}
          chips={monthlyPulse.chips}
          title={monthlyPulse.title}
        />

        <section
          aria-label="Métricas principales"
          className="grid gap-5 md:grid-cols-2 xl:grid-cols-4"
        >
          {dashboardMetrics.map((metric) => (
            <MetricCard key={metric.id} metric={metric} />
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(23rem,0.8fr)]">
          <PlanVsRealChart data={planVsRealSeries} />
          <UpcomingPayments payments={upcomingPayments} />
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <InsightCard insight={suggestedAction} />
          <InsightCard insight={attentionInsight} />
        </section>
      </div>
    </AppShell>
  );
}
