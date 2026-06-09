import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeTone = "positive" | "brand" | "warning" | "risk" | "neutral";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone;
};

const tones: Record<BadgeTone, string> = {
  positive: "bg-positiveSoft text-positive",
  brand: "bg-brandSoft text-brand",
  warning: "bg-warningSoft text-warning",
  risk: "bg-riskSoft text-risk",
  neutral: "bg-background text-secondary",
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
