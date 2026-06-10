import { PageIntro } from "@/components/finance/PageIntro";
import { PageFrame } from "@/components/layout/PageFrame";

export default function AlertsPage() {
  return (
    <PageFrame title="Alertas">
      <PageIntro
        body="Por ahora las alertas salen del plan, pagos en revisión y gastos fuera de plan. La capa proactiva real llegará cuando se conecte la API."
        title="¿Qué requiere atención?"
      />
    </PageFrame>
  );
}
