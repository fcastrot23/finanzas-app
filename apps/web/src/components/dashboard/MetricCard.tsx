import {
  CalendarDays,
  CreditCard,
  ShieldCheck,
  Sprout,
  type LucideIcon,
} from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { DashboardMetric } from "@/types/finance";

type MetricCardProps = {
  metric: DashboardMetric;
};

const iconByMetric: Record<string, LucideIcon> = {
  "available-buffer": ShieldCheck,
  "next-payment": CalendarDays,
  "priority-debt": CreditCard,
  leisure: Sprout,
};

const toneClassName: Record<DashboardMetric["tone"], string> = {
  positive: "bg-positiveSoft text-positive",
  brand: "bg-brandSoft text-brand",
  warning: "bg-warningSoft text-warning",
  risk: "bg-riskSoft text-risk",
};

export function MetricCard({ metric }: MetricCardProps) {
  const Icon = iconByMetric[metric.id] ?? ShieldCheck;

  return (
    <Card className="flex min-h-36 items-center gap-4 p-6">
      <div
        className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full ${toneClassName[metric.tone]}`}
      >
        <Icon aria-hidden="true" className="h-7 w-7" />
      </div>
      <div className="min-w-0 space-y-2">
        <p className="text-sm font-medium text-secondary">{metric.title}</p>
        <p className="text-xl font-semibold leading-tight text-primary">
          {metric.value}
        </p>
        <p className="text-sm text-secondary">{metric.helper}</p>
      </div>
    </Card>
  );
}
