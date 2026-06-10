import type { ReactNode } from "react";

import type { HouseholdMember } from "@/types/finance";

type TopBarProps = {
  members: HouseholdMember[];
  title?: string;
  subtitle?: string;
  action?: ReactNode;
};

export function TopBar({
  members,
  title = "Resumen del hogar",
  subtitle = "Hogar Fau & Mari",
  action,
}: TopBarProps) {
  return (
    <header className="flex flex-col gap-5 pb-6 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 className="text-3xl font-semibold tracking-normal text-primary">
          {title}
        </h1>
        <p className="mt-2 text-base text-secondary">{subtitle}</p>
      </div>

      <div className="flex flex-col gap-4 sm:items-end">
        {action}
        <div className="flex items-center gap-5">
        {members.map((member) => (
          <div key={member.id} className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brandSoft text-sm font-semibold text-brand">
              {member.name.slice(0, 1)}
            </div>
            <div>
              <p className="text-sm font-semibold text-primary">{member.name}</p>
              <p className="text-sm text-secondary">
                {member.defaultCurrency === "USD" ? "$ USD" : "₡ CRC"}
              </p>
            </div>
          </div>
        ))}
        </div>
      </div>
    </header>
  );
}
