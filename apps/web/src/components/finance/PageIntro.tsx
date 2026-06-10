type PageIntroProps = {
  title: string;
  body: string;
};

export function PageIntro({ title, body }: PageIntroProps) {
  return (
    <div className="rounded-card border border-border bg-surface p-5 shadow-soft">
      <p className="text-sm font-semibold text-brand">{title}</p>
      <p className="mt-2 text-sm leading-6 text-secondary">{body}</p>
    </div>
  );
}
