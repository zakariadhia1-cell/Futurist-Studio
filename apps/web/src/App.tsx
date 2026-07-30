import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { RequireAuth } from '@/components/layout/RequireAuth'
import { AgentsPage } from '@/app/agents/AgentsPage'
import { AutomationsPage } from '@/app/automations/AutomationsPage'
import { BrowserPage } from '@/app/browser/BrowserPage'
import { ChatPage } from '@/app/chat/ChatPage'
import { DashboardPage } from '@/app/dashboard/DashboardPage'
import { FilesPage } from '@/app/files/FilesPage'
import { KnowledgePage } from '@/app/knowledge/KnowledgePage'
import { LoginPage } from '@/app/login/LoginPage'
import { ProjectsPage } from '@/app/projects/ProjectsPage'
import { SettingsPage } from '@/app/settings/SettingsPage'
import { TasksPage } from '@/app/tasks/TasksPage'
import { TerminalPage } from '@/app/terminal/TerminalPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="tasks" element={<TasksPage />} />
            <Route path="files" element={<FilesPage />} />
            <Route path="knowledge" element={<KnowledgePage />} />
            <Route path="automations" element={<AutomationsPage />} />
            <Route path="browser" element={<BrowserPage />} />
            <Route path="terminal" element={<TerminalPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
