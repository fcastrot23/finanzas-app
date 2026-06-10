"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { X } from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusChip } from "@/components/ui/StatusChip";
import {
  leisureBudgets,
  monthlyPlanBaseline,
  pockets,
  realTransactions,
} from "@/data/mock-finance";
import { formatCompactMoney } from "@/lib/finance/currency";
import { evaluateSpendingGuardrail } from "@/lib/finance/spending-guardrail";
import type { SpendingGuardrailResult } from "@/types/finance";

const guardrailSchema = z.object({
  amount: z.coerce.number().positive(),
  currency: z.enum(["CRC", "USD"]),
  concept: z.string().min(2),
  pocketId: z.string().min(1),
  paidById: z.string().min(1),
  shared: z.coerce.boolean(),
});

type GuardrailForm = z.infer<typeof guardrailSchema>;

const toneToChip = {
  green: "positive",
  amber: "warning",
  red: "risk",
} as const;

export function SpendingGuardrailModal() {
  const [open, setOpen] = useState(false);
  const [result, setResult] = useState<SpendingGuardrailResult | null>(null);
  const { register, handleSubmit, watch } = useForm<GuardrailForm>({
    resolver: zodResolver(guardrailSchema),
    defaultValues: {
      amount: 10000,
      currency: "CRC",
      concept: "Salida familiar",
      pocketId: "hogar-crc-leisure",
      paidById: "fau",
      shared: true,
    },
  });
  const selectedCurrency = watch("currency");
  const availablePockets = useMemo(
    () => pockets.filter((pocket) => pocket.currency === selectedCurrency),
    [selectedCurrency],
  );

  function onSubmit(values: GuardrailForm) {
    setResult(
      evaluateSpendingGuardrail(values, {
        pockets,
        leisureBudgets,
        plannedPayments: monthlyPlanBaseline.items,
        transactions: realTransactions,
      }),
    );
  }

  return (
    <>
      <Button onClick={() => setOpen(true)} variant="secondary">
        ¿Puedo gastar esto?
      </Button>

      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-primary/20 p-4">
          <Card className="max-h-[90vh] w-full max-w-2xl overflow-y-auto p-6">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-primary">
                  ¿Puedo gastar esto?
                </h2>
                <p className="mt-2 text-sm text-secondary">
                  Evaluá el impacto antes de comprometer dinero real.
                </p>
              </div>
              <button
                aria-label="Cerrar"
                className="rounded-lg p-2 text-secondary hover:bg-background hover:text-primary"
                onClick={() => setOpen(false)}
                type="button"
              >
                <X aria-hidden="true" className="h-5 w-5" />
              </button>
            </div>

            <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
              <label className="space-y-2 text-sm font-medium text-primary">
                Monto
                <input
                  className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                  {...register("amount")}
                />
              </label>
              <label className="space-y-2 text-sm font-medium text-primary">
                Moneda
                <select
                  className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                  {...register("currency")}
                >
                  <option value="CRC">CRC</option>
                  <option value="USD">USD</option>
                </select>
              </label>
              <label className="space-y-2 text-sm font-medium text-primary">
                Concepto
                <input
                  className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                  {...register("concept")}
                />
              </label>
              <label className="space-y-2 text-sm font-medium text-primary">
                Bolsillo
                <select
                  className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                  {...register("pocketId")}
                >
                  {availablePockets.map((pocket) => (
                    <option key={pocket.id} value={pocket.id}>
                      {pocket.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-2 text-sm font-medium text-primary">
                Pagado por
                <select
                  className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                  {...register("paidById")}
                >
                  <option value="fau">Fau</option>
                  <option value="mari">Mari</option>
                </select>
              </label>
              <label className="flex items-center gap-3 self-end rounded-lg border border-border px-3 py-3 text-sm font-medium text-primary">
                <input
                  className="h-4 w-4 accent-brand"
                  type="checkbox"
                  {...register("shared")}
                />
                Es gasto compartido
              </label>
              <div className="flex gap-3 sm:col-span-2">
                <Button type="submit">Evaluar</Button>
                <Button onClick={() => setOpen(false)} type="button" variant="ghost">
                  Cancelar
                </Button>
              </div>
            </form>

            {result ? (
              <div className="mt-6 rounded-card border border-border bg-background p-5">
                <StatusChip tone={toneToChip[result.tone]}>{result.title}</StatusChip>
                <dl className="mt-4 grid gap-4 sm:grid-cols-3">
                  <ResultItem
                    label="Colchón restante"
                    value={formatCompactMoney(
                      result.remainingCushion,
                      result.currency,
                    )}
                  />
                  <ResultItem label="Qué sacrifica" value={result.sacrificed} />
                  <ResultItem
                    label="Aprobación"
                    value={result.requiresApproval ? "Requiere acuerdo" : "No requiere"}
                  />
                </dl>
              </div>
            ) : null}
          </Card>
        </div>
      ) : null}
    </>
  );
}

function ResultItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-normal text-secondary">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-semibold text-primary">{value}</dd>
    </div>
  );
}
