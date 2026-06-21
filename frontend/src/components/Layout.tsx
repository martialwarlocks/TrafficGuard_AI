import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, Monitor, ClipboardCheck, FileSearch, BarChart3,
  Map, Cpu, Settings, LogOut, Shield, Bell, ChevronLeft,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore, useAppStore } from '@/store'
import { Badge } from './ui'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/monitoring', icon: Monitor, label: 'Live Monitoring' },
  { to: '/review', icon: ClipboardCheck, label: 'Human Review' },
  { to: '/evidence', icon: FileSearch, label: 'Evidence' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/digital-twin', icon: Map, label: 'Digital Twin' },
  { to: '/model', icon: Cpu, label: 'Model Monitor' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function DashboardLayout() {
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, toggleSidebar, alerts } = useAppStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-bg overflow-hidden">
      <motion.aside
        animate={{ width: sidebarCollapsed ? 64 : 240 }}
        className="flex flex-col border-r border-border bg-card/50 shrink-0"
      >
        <div className="flex items-center gap-2 p-4 border-b border-border">
          <Shield className="w-8 h-8 text-primary shrink-0" />
          {!sidebarCollapsed && (
            <div>
              <h1 className="font-bold text-sm">TrafficGuard AI</h1>
              <p className="text-[10px] text-muted">Confident Enforcement</p>
            </div>
          )}
        </div>

        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                  isActive ? 'bg-primary/15 text-primary' : 'text-muted hover:text-text hover:bg-card'
                )
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!sidebarCollapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="p-2 border-t border-border">
          <button
            onClick={toggleSidebar}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-muted hover:text-text hover:bg-card text-sm"
          >
            <ChevronLeft className={cn('w-5 h-5 transition-transform', sidebarCollapsed && 'rotate-180')} />
            {!sidebarCollapsed && <span>Collapse</span>}
          </button>
        </div>
      </motion.aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex items-center justify-between px-6 py-3 border-b border-border bg-card/30">
          <div />
          <div className="flex items-center gap-4">
            <div className="relative">
              <Bell className="w-5 h-5 text-muted" />
              {alerts.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-danger rounded-full text-[10px] flex items-center justify-center">
                  {alerts.length}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-sm font-bold">
                {user?.full_name?.[0] || 'U'}
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-medium">{user?.full_name}</p>
                <Badge variant="muted">{user?.role}</Badge>
              </div>
            </div>
            <button onClick={handleLogout} className="text-muted hover:text-danger transition-colors">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
