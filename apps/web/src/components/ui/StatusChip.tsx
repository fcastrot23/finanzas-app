import { AlertTriangle, CheckCircle2, Clock3, ShieldCheck } from "lucide-react";
import type { ComponentType, HTMLAttributes, SVGProps } from "react";

import { cn } from "@/lib/utils";

type StatusTone = "positive" | "brand" | "warning" | "risk";

type StatusChipProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: StatusTone;
};

const tones: Record<
  StatusTone,
  {
    className: string;
    icon: ComponentType<SVGProps<SVGSVGElement>>;
  }
> = {
  positive: {
    className: "bg-positiveSoft text-positive",
    icon: ShieldCheck,
  },
  brand: {
    className: "bg-brandSoft text-brand",
    icon: CheckCircle2,
  },
  warning: {
    className: "bg-warningSoft text-warning",
    icon: Clock3,
  },
  risk: {
    className: "bg-riskSoft text-risk",
    icon: AlertTriangle,
  },
};

export function StatusChip({
  className,
  tone = "positive",
  children,
  ...props
}: StatusChipProps) {
  const Icon = tones[tone].icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium",
        tones[tone].className,
        className,
      )}
      {...props}
    >
      <Icon aria-hidden="true" className="h-4 w-4" />
      {children}
    </span>
  );
}
