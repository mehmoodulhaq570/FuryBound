/** A centred title and message for loading, sign-in and error states. */
export function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-xl space-y-3">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <div className="text-muted space-y-3">{children}</div>
    </div>
  );
}
