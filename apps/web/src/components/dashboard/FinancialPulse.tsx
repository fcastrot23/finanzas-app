import { Sparkles } from "lucide-react";

import { Card } from "@/components/ui/Card";
import { StatusChip } from "@/components/ui/StatusChip";

type FinancialPulseProps = {
  title: string;
  body: string;
  chips: string[];
};

const chipTone = ["positive", "brand", "warning"] as const;

export function FinancialPulse({ title, body, chips }: FinancialPulseProps) {
  return (
    <Card className="flex flex-col gap-5 p-6 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brandSoft text-brand">
          <Sparkles aria-hidden="true" className="h-6 w-6" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-primary">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-secondary">{body}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        {chips.map((chip, index) => (
          <StatusChip key={chip} tone={chipTone[index] ?? "positive"}>
            {chip}
          </StatusChip>
        ))}
      </div>
    </Card>
  );
}
