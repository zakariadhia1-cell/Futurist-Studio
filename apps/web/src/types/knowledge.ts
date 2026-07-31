export interface KnowledgeDocument {
  id: string
  title: string
  source_type: string
  created_at: string
}

export interface SearchChunkResult {
  document_id: string
  document_title: string
  content: string
  distance: number
}
