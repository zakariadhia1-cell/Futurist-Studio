export interface FileEntry {
  id: string
  filename: string
  content_type: string
  size_bytes: number
  source: 'upload' | 'generated'
  created_at: string
  updated_at: string
}

export interface Note {
  id: string
  title: string
  content: string
  created_at: string
  updated_at: string
}
