import { CheckCircle2, CircleDashed } from "lucide-react";

import { PageIntro } from "@/components/finance/PageIntro";
import { PageFrame } from "@/components/layout/PageFrame";
import { Card } from "@/components/ui/Card";
import { StatusChip } from "@/components/ui/StatusChip";
import { householdMembers, monthlyPlanBaseline, pockets } from "@/data/mock-finance";

const onboardingSteps = [
  {
    title: "Personas del hogar",
    body: "Fau y Mari están listos para construir el plan compartido.",
    done: householdMembers.length > 1,
  },
  {
    title: "Bolsillos separados",
    body: "Hay bolsillos por persona, hogar y moneda.",
    done: pockets.length > 0,
  },
  {
    title: "Plan baseline",
    body: "Junio tiene un plan aprobado que no se modifica con transacciones reales.",
    done: monthlyPlanBaseline.items.length > 0,
  },
  {
    title: "Revisión final",
    body: "Confirmar escuela y servicios antes de cerrar la semana.",
    done: false,
  },
];

export default function OnboardingPage() {
  return (
    <PageFrame title="Onboarding">
      <div className="space-y-6">
      <PageIntro
        body="La app necesita personas, bolsillos y plan baseline antes de comparar el dinero real."
        title="¿Qué información falta para crear mi plan?"
      />
      <div className="grid gap-4 md:grid-cols-2">
        {onboardingSteps.map((step) => {
          const Icon = step.done ? CheckCircle2 : CircleDashed;

          return (
            <Card className="flex gap-4 p-5" key={step.title}>
              <div className="mt-1 text-brand">
                <Icon aria-hidden="true" className="h-6 w-6" />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="font-semibold text-primary">{step.title}</h2>
                  <StatusChip tone={step.done ? "positive" : "warning"}>
                    {step.done ? "Listo" : "Pendiente"}
                  </StatusChip>
                </div>
                <p className="mt-2 text-sm leading-6 text-secondary">{step.body}</p>
              </div>
            </Card>
          );
        })}
      </div>
      </div>
    </PageFrame>
  );
}
