import type { ReactNode } from "react";

import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

type FinanceTableColumn<T> = {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
  align?: "left" | "right";
};

type FinanceTableProps<T> = {
  columns: FinanceTableColumn<T>[];
  rows: T[];
  getRowKey: (row: T) => string;
};

export function FinanceTable<T>({
  columns,
  rows,
  getRowKey,
}: FinanceTableProps<T>) {
  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[42rem] border-collapse text-left text-sm">
          <thead className="bg-background text-xs uppercase tracking-normal text-secondary">
            <tr>
              {columns.map((column) => (
                <th
                  className={cn(
                    "px-5 py-4 font-semibold",
                    column.align === "right" && "text-right",
                  )}
                  key={column.key}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => (
              <tr key={getRowKey(row)}>
                {columns.map((column) => (
                  <td
                    className={cn(
                      "px-5 py-4 text-primary",
                      column.align === "right" && "text-right",
                    )}
                    key={column.key}
                  >
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
