export function EmptyState({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center rounded-xl border border-dashed border-border text-center">
      <div className="font-mono text-xs uppercase tracking-wider text-text-low">{phase}</div>
      <div className="mt-2 text-text-mid">{title}</div>
    </div>
  )
}
