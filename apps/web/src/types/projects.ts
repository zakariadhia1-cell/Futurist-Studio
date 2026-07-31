export interface Project {
  id: string
  name: string
  description: string | null
  status: 'active' | 'paused' | 'done' | 'archived'
  color: string | null
  created_at: string
  updated_at: string
}

export interface Task {
  id: string
  project_id: string | null
  title: string
  description: string | null
  status: 'todo' | 'in_progress' | 'done'
  priority: 'low' | 'medium' | 'high'
  due_date: string | null
  created_at: string
  updated_at: string
}
