import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function KnowledgePage() {
  return (
    <>
      <PageHeader title="Wissensdatenbank" />
      <EmptyState title="Wissensdatenbank ist noch nicht implementiert." phase="Kommt in Phase 2 - Wissensdatenbank & Gedaechtnis" />
    </>
  )
}
