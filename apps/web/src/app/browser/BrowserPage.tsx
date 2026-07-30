import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function BrowserPage() {
  return (
    <>
      <PageHeader title="Browser" />
      <EmptyState title="Browser ist noch nicht implementiert." phase="Kommt in Phase 4 - Browser- & Terminalsteuerung" />
    </>
  )
}
