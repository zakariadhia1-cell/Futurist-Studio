import { Loader2 } from 'lucide-react'

export function LoadingState({ label = 'Lade Daten...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2.5 py-16 text-white/40">
      <Loader2 className="h-4 w-4 animate-spin" strokeWidth={1.75} />
      <span className="font-mono text-xs uppercase tracking-wider">{label}</span>
    </div>
  )
}
