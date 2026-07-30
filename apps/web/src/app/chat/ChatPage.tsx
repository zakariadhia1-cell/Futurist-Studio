import { PageHeader } from '@/components/layout/PageHeader'
import { EmptyState } from '@/components/layout/EmptyState'

export function ChatPage() {
  return (
    <>
      <PageHeader title="Chat" />
      <EmptyState title="Chat ist noch nicht implementiert." phase="Kommt in Phase 1 - Core Chat" />
    </>
  )
}
