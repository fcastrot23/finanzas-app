"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { formatCompactMoney } from "@/lib/finance/currency";
import { getPlanVsRealDelta } from "@/lib/finance/dashboard-summary";
import type { PlanVsRealPoint } from "@/types/finance";

type PlanVsRealChartProps = {
  data: PlanVsRealPoint[];
};

export function PlanVsRealChart({ data }: PlanVsRealChartProps) {
  const delta = getPlanVsRealDelta(data);
  const currency = delta.currency ?? "CRC";

  return (
    <Card className="p-6">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle>Plan vs Real</CardTitle>
          <CardDescription>
            Comparación acumulada en {currency}; el baseline no se modifica.
          </CardDescription>
        </div>
        <p className="max-w-sm text-sm text-secondary">
          Proyección: cerrás dentro del plan si mantenés este ritmo.
        </p>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
            <CartesianGrid stroke="#E5E7EB" strokeDasharray="4 4" vertical={false} />
            <XAxis
              axisLine={false}
              dataKey="label"
              tickLine={false}
              tick={{ fill: "#64748B", fontSize: 12 }}
            />
            <YAxis
              axisLine={false}
              tickFormatter={(value) => formatCompactMoney(Number(value), currency)}
              tickLine={false}
              tick={{ fill: "#64748B", fontSize: 12 }}
              width={78}
            />
            <Tooltip
              contentStyle={{
                borderColor: "#E5E7EB",
                borderRadius: "12px",
                boxShadow: "0 10px 30px rgba(15, 23, 42, 0.06)",
              }}
              formatter={(value) => formatCompactMoney(Number(value), currency)}
              labelStyle={{ color: "#0F172A", fontWeight: 600 }}
            />
            <Line
              dataKey="plan"
              dot={false}
              name="Plan"
              stroke="#2536D9"
              strokeWidth={3}
              type="monotone"
            />
            <Line
              dataKey="real"
              dot={false}
              name="Real"
              stroke="#059669"
              strokeDasharray="8 8"
              strokeWidth={3}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-5 grid gap-4 rounded-lg border border-border p-4 sm:grid-cols-3">
        <SummaryItem
          label="Diferencia vs plan"
          value={`${formatCompactMoney(delta.amount, currency)} por debajo`}
        />
        <SummaryItem label="Categoría principal" value="Ocio" />
        <SummaryItem label="Proyección" value="Dentro del plan" />
      </div>
    </Card>
  );
}

type SummaryItemProps = {
  label: string;
  value: string;
};

function SummaryItem({ label, value }: SummaryItemProps) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-normal text-secondary">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-primary">{value}</p>
    </div>
  );
}
