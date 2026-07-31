import {
  ActivitySquare,
  BarChart3,
  Bell,
  Bot,
  FolderKanban,
  LayoutDashboard,
  ListChecks,
  MessageSquare,
  Settings,
  ShoppingBag,
  UtensilsCrossed,
  Workflow,
  type LucideIcon,
} from 'lucide-react'

export interface OsNavItem {
  to: string
  label: string
  icon: LucideIcon
}

export const OS_NAV: OsNavItem[] = [
  { to: '/os/overview', label: 'Uebersicht', icon: LayoutDashboard },
  { to: '/os/agents', label: 'KI-Agenten', icon: Bot },
  { to: '/os/tasks', label: 'Aufgaben', icon: ListChecks },
  { to: '/os/projects', label: 'Projekte', icon: FolderKanban },
  { to: '/os/shopify', label: 'Shopify', icon: ShoppingBag },
  { to: '/os/gastro', label: 'Gastro Prinz', icon: UtensilsCrossed },
  { to: '/os/chat', label: 'KI-Chat', icon: MessageSquare },
  { to: '/os/automations', label: 'Automationen', icon: Workflow },
  { to: '/os/monitoring', label: 'Systemueberwachung', icon: ActivitySquare },
  { to: '/os/notifications', label: 'Benachrichtigungen', icon: Bell },
  { to: '/os/analytics', label: 'Analysen', icon: BarChart3 },
  { to: '/os/settings', label: 'Einstellungen', icon: Settings },
]
