import { CalendarDays, Car, GraduationCap, Home } from "lucide-react";

import { Card, CardTitle } from "@/components/ui/Card";
import { StatusChip } from "@/components/ui/StatusChip";
import { formatCompactMoney } from "@/lib/finance/currency";
import type { PaymentStatus, PlannedPayment } from "@/types/finance";

type UpcomingPaymentsProps = {
  payments: PlannedPayment[];
};

const paymentIcon = {
  Carro: Car,
  Hipoteca: Home,
  Escuela: GraduationCap,
};

const statusLabels: Record<PaymentStatus, string> = {
  paid: "Listo",
  upcoming: "Próximo",
  review: "Revisar",
  overdue: "Atrasado",
};

const statusTones: Record<PaymentStatus, "positive" | "brand" | "warning" | "risk"> = {
  paid: "positive",
  upcoming: "brand",
  review: "warning",
  overdue: "risk",
};

export function UpcomingPayments({ payments }: UpcomingPaymentsProps) {
  return (
    <Card className="p-6">
      <div className="mb-6 flex items-center justify-between gap-4">
        <CardTitle>Próximos pagos</CardTitle>
        <CalendarDays aria-hidden="true" className="h-5 w-5 text-secondary" />
      </div>

      <div className="divide-y divide-border">
        {payments.map((payment) => {
          const Icon = paymentIcon[payment.concept as keyof typeof paymentIcon] ?? CalendarDays;

          return (
            <div
              className="grid grid-cols-[3.5rem_1fr] gap-4 py-4 first:pt-0 last:pb-0"
              key={payment.id}
            >
              <DateBadge date={payment.date} />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-positiveSoft text-positive">
                    <Icon aria-hidden="true" className="h-6 w-6" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-primary">{payment.concept}</p>
                    <p className="text-sm text-secondary">{payment.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 sm:justify-end">
                  <p className="text-sm font-semibold text-primary">
                    {formatCompactMoney(payment.amount, payment.currency)}
                  </p>
                  <StatusChip tone={statusTones[payment.status]}>
                    {statusLabels[payment.status]}
                  </StatusChip>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function DateBadge({ date }: { date: string }) {
  const formatted = new Intl.DateTimeFormat("es-CR", {
    day: "2-digit",
    month: "short",
    timeZone: "UTC",
  })
    .format(new Date(date))
    .replace(".", "")
    .split(" ");

  return (
    <div className="flex h-14 w-14 flex-col items-center justify-center rounded-lg bg-background text-center">
      <span className="text-lg font-semibold leading-none text-primary">{formatted[0]}</span>
      <span className="mt-1 text-xs font-medium uppercase text-secondary">
        {formatted[1]}
      </span>
    </div>
  );
}
