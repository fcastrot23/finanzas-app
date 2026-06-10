import type { HouseholdMember } from "@/types/finance";

type TopBarProps = {
  members: HouseholdMember[];
};

export function TopBar({ members }: TopBarProps) {
  return (
    <header className="flex flex-col gap-5 pb-6 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 className="text-3xl font-semibold tracking-normal text-primary">
          Resumen del hogar
        </h1>
        <p className="mt-2 text-base text-secondary">Hogar Fau & Mari</p>
      </div>

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
    </header>
  );
}
