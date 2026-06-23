import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { DashboardLayout } from '@/components/Layout'
import { LandingPage } from '@/pages/LandingPage'
import { LoginPage, SignupPage, ForgotPasswordPage } from '@/pages/AuthPages'
import { DashboardPage } from '@/pages/DashboardPage'
import { MonitoringPage } from '@/pages/MonitoringPage'
import { ReviewPage } from '@/pages/ReviewPage'
import { EvidencePage } from '@/pages/EvidencePage'
import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { DigitalTwinPage } from '@/pages/DigitalTwinPage'
import { ModelMonitorPage } from '@/pages/ModelMonitorPage'
import { LiveTestPage } from '@/pages/LiveTestPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { useAuthStore } from '@/store'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="monitoring" element={<MonitoringPage />} />
        <Route path="live-test" element={<LiveTestPage />} />
        <Route path="review" element={<ReviewPage />} />
        <Route path="evidence" element={<EvidencePage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="digital-twin" element={<DigitalTwinPage />} />
        <Route path="model" element={<ModelMonitorPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
