import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function AutomationsPage() {
  return (
    <>
      <PageHeader title="Automationen" />
      <EmptyState title="Automationen ist noch nicht implementiert." phase="Kommt in Phase 5 - Restliche Fachagenten (n8n)" />
    </>
  )
}
