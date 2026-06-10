import type { ReactNode } from "react";

import { householdMembers } from "@/data/mock-finance";
import { AppShell } from "@/components/layout/AppShell";
import { TopBar } from "@/components/layout/TopBar";

type PageFrameProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function PageFrame({
  title,
  subtitle = "Hogar Fau & Mari",
  children,
}: PageFrameProps) {
  return (
    <AppShell>
      <TopBar members={householdMembers} subtitle={subtitle} title={title} />
      {children}
    </AppShell>
  );
}
