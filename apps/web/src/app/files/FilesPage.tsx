import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function FilesPage() {
  return (
    <>
      <PageHeader title="Dateien" />
      <EmptyState title="Dateien ist noch nicht implementiert." phase="Kommt in Phase 7 - Dateien, Notizen, Kalender, E-Mail" />
    </>
  )
}
