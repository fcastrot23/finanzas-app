type SectionHeaderProps = {
  title: string;
  description?: string;
};

export function SectionHeader({ title, description }: SectionHeaderProps) {
  return (
    <div className="space-y-1">
      <h2 className="text-lg font-semibold text-primary">{title}</h2>
      {description ? <p className="text-sm text-secondary">{description}</p> : null}
    </div>
  );
}
