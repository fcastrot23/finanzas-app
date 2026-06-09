import { AlertTriangle, ArrowRight, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { Insight } from "@/types/finance";

type InsightCardProps = {
  insight: Insight;
};

const toneClassName: Record<Insight["tone"], string> = {
  positive: "bg-positiveSoft text-positive",
  warning: "bg-warningSoft text-warning",
  risk: "bg-riskSoft text-risk",
};

const iconByTone = {
  positive: TrendingUp,
  warning: AlertTriangle,
  risk: AlertTriangle,
};

export function InsightCard({ insight }: InsightCardProps) {
  const Icon = iconByTone[insight.tone];

  return (
    <Card className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center">
      <div
        className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full ${toneClassName[insight.tone]}`}
      >
        <Icon aria-hidden="true" className="h-7 w-7" />
      </div>
      <div className="min-w-0 flex-1">
        <h2 className="text-lg font-semibold text-primary">{insight.title}</h2>
        <p className="mt-2 text-sm leading-6 text-secondary">{insight.body}</p>
      </div>
      {insight.actionLabel ? (
        <Button
          className="w-full sm:w-auto"
          icon={<ArrowRight aria-hidden="true" className="h-4 w-4" />}
          variant={insight.tone === "risk" ? "risk" : "secondary"}
        >
          {insight.actionLabel}
        </Button>
      ) : null}
    </Card>
  );
}
