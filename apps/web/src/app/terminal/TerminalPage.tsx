import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function TerminalPage() {
  return (
    <>
      <PageHeader title="Terminal" />
      <EmptyState title="Terminal ist noch nicht implementiert." phase="Kommt in Phase 4 - Browser- & Terminalsteuerung" />
    </>
  )
}
