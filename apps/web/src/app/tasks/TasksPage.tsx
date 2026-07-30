import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function TasksPage() {
  return (
    <>
      <PageHeader title="Aufgaben" />
      <EmptyState title="Aufgaben ist noch nicht implementiert." phase="Kommt in Phase 3 - Multi-Agent-Orchestrierung" />
    </>
  )
}
