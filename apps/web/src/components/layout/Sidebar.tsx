import {
  Bell,
  CalendarDays,
  CreditCard,
  Goal,
  Home,
  Landmark,
  LayoutDashboard,
  PieChart,
  Settings,
  UsersRound,
  WalletCards,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const navigationItems = [
  { label: "Resumen", icon: LayoutDashboard, active: true },
  { label: "Plan", icon: CalendarDays },
  { label: "Transacciones", icon: CreditCard },
  { label: "Bolsillos", icon: WalletCards },
  { label: "Presupuestos", icon: PieChart },
  { label: "Deudas", icon: Landmark },
  { label: "Metas", icon: Goal },
  { label: "Alertas", icon: Bell },
];

const secondaryItems = [
  { label: "Hogar", icon: UsersRound },
  { label: "Configuración", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-72 shrink-0 border-r border-border bg-surface px-5 py-7 lg:flex lg:flex-col">
      <div className="mb-9 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand text-white">
          <Home aria-hidden="true" className="h-6 w-6" />
        </div>
        <span className="text-xl font-semibold text-primary">
          Hogar<span className="text-brand">Claro</span>
        </span>
      </div>

      <nav className="space-y-2" aria-label="Navegación principal">
        {navigationItems.map((item) => (
          <SidebarItem key={item.label} {...item} />
        ))}
      </nav>

      <div className="my-7 h-px bg-border" />

      <nav className="space-y-2" aria-label="Navegación del hogar">
        {secondaryItems.map((item) => (
          <SidebarItem key={item.label} {...item} />
        ))}
      </nav>

      <div className="mt-auto rounded-card border border-border bg-background p-4">
        <p className="text-sm font-semibold text-primary">Asistente tranquilo</p>
        <p className="mt-2 text-xs leading-5 text-secondary">
          Preguntá antes de mover dinero o cambiar un pago.
        </p>
        <Button className="mt-4 w-full" variant="secondary">
          Preguntar
        </Button>
      </div>
    </aside>
  );
}

type SidebarItemProps = {
  label: string;
  icon: typeof LayoutDashboard;
  active?: boolean;
};

function SidebarItem({ label, icon: Icon, active }: SidebarItemProps) {
  return (
    <a
      className={cn(
        "flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-secondary transition-colors hover:bg-brandSoft hover:text-brand",
        active && "bg-brandSoft text-brand",
      )}
      href="#"
    >
      <Icon aria-hidden="true" className="h-5 w-5" />
      {label}
    </a>
  );
}
