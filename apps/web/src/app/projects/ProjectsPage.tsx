import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function ProjectsPage() {
  return (
    <>
      <PageHeader title="Projekte" />
      <EmptyState title="Projekte ist noch nicht implementiert." phase="Kommt in Phase 3 - Multi-Agent-Orchestrierung" />
    </>
  )
}
