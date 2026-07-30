export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="mb-6">
      <h1 className="text-xl font-semibold text-text-hi">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-text-mid">{subtitle}</p>}
    </header>
  )
}
