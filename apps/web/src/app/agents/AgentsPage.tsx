import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function AgentsPage() {
  return (
    <>
      <PageHeader title="Agenten" />
      <EmptyState title="Agenten ist noch nicht implementiert." phase="Kommt in Phase 3 - Multi-Agent-Orchestrierung" />
    </>
  )
}
