import { create } from 'zustand'
import { api } from '@/lib/api'

interface User {
  id: number
  email: string
  full_name: string
  role: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('tg_token'),
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const { access_token } = await api.login(email, password)
      api.setToken(access_token)
      const user = await api.getMe()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (e) {
      set({ isLoading: false })
      throw e
    }
  },

  logout: () => {
    api.setToken(null)
    set({ user: null, isAuthenticated: false })
  },

  checkAuth: async () => {
    if (!localStorage.getItem('tg_token')) return
    try {
      const user = await api.getMe()
      set({ user, isAuthenticated: true })
    } catch {
      api.setToken(null)
      set({ user: null, isAuthenticated: false })
    }
  },
}))

interface Alert {
  id: string
  title: string
  message: string
  type: 'info' | 'warning' | 'danger' | 'success'
  timestamp: Date
}

interface AppState {
  alerts: Alert[]
  addAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void
  removeAlert: (id: string) => void
  sidebarCollapsed: boolean
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>((set) => ({
  alerts: [],
  sidebarCollapsed: false,

  addAlert: (alert) =>
    set((s) => ({
      alerts: [{ ...alert, id: crypto.randomUUID(), timestamp: new Date() }, ...s.alerts].slice(0, 20),
    })),

  removeAlert: (id) => set((s) => ({ alerts: s.alerts.filter((a) => a.id !== id) })),

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}))
