import { FinanceTable } from "@/components/finance/FinanceTable";
import { PageIntro } from "@/components/finance/PageIntro";
import { PageFrame } from "@/components/layout/PageFrame";
import { StatusChip } from "@/components/ui/StatusChip";
import { pockets, realTransactions } from "@/data/mock-finance";
import { formatCompactMoney } from "@/lib/finance/currency";
import { calculateCurrentBalance } from "@/lib/finance/running-balance";
import type { Pocket } from "@/types/finance";

const purposeLabel = {
  income: "Ingresos",
  buffer: "Colchón",
  bills: "Pagos",
  leisure: "Ocio",
  debt: "Deudas",
  emergency: "Emergencia",
};

export default function PocketsPage() {
  return (
    <PageFrame title="Bolsillos">
      <div className="space-y-6">
      <PageIntro
        body="Cada bolsillo pertenece a una persona o al hogar y tiene una sola moneda."
        title="¿Dónde está el dinero disponible?"
      />
      <FinanceTable<Pocket>
        columns={[
          {
            key: "name",
            label: "Bolsillo",
            render: (row) => (
              <div>
                <p className="font-semibold">{row.name}</p>
                <p className="text-secondary">
                  {row.ownerType === "household" ? "Hogar" : row.ownerId === "fau" ? "Fau" : "Mari"}
                </p>
              </div>
            ),
          },
          {
            key: "currency",
            label: "Moneda",
            render: (row) => <StatusChip tone="brand">{row.currency}</StatusChip>,
          },
          {
            key: "purpose",
            label: "Uso",
            render: (row) => purposeLabel[row.purpose],
          },
          {
            key: "balance",
            label: "Saldo actual",
            align: "right",
            render: (row) =>
              formatCompactMoney(
                calculateCurrentBalance(row, realTransactions),
                row.currency,
              ),
          },
        ]}
        getRowKey={(row) => row.id}
        rows={pockets}
      />
      </div>
    </PageFrame>
  );
}
