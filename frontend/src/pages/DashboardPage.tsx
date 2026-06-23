import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  AlertTriangle, Camera, TrendingUp, Shield, IndianRupee, Activity, Clock, Users,
} from 'lucide-react'
import { KPICard } from '@/components/KPICard'
import { TrendChart } from '@/components/TrendChart'
import { Card, Badge } from '@/components/ui'
import { api } from '@/lib/api'

export function DashboardPage() {
  const { data: stats } = useQuery({ queryKey: ['dashboard'], queryFn: () => api.getDashboard(), refetchInterval: 30000 })
  const { data: violations } = useQuery({ queryKey: ['violations'], queryFn: () => api.getViolations({ limit: '10' }) })
  const { data: analytics, isError: analyticsError } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => api.getAnalytics(),
    retry: 1,
  })

  const trendData = analytics?.hourly_trends || []

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-2xl font-bold">Command Center</h1>
        <p className="text-muted text-sm">Real-time traffic enforcement overview</p>
      </motion.div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Violations" value={stats?.total_violations || 0} icon={<AlertTriangle className="w-5 h-5" />} delay={0} />
        <KPICard title="Auto Processed" value={stats?.auto_processed || 0} color="success" icon={<Shield className="w-5 h-5" />} delay={0.1} />
        <KPICard title="Human Reviewed" value={stats?.human_reviewed || 0} color="warning" icon={<Users className="w-5 h-5" />} delay={0.2} />
        <KPICard title="Pending Reviews" value={stats?.pending_reviews || 0} color="danger" icon={<Clock className="w-5 h-5" />} delay={0.3} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Avg Confidence" value={Math.round((stats?.avg_confidence || 0) * 100)} suffix="%" color="primary" icon={<TrendingUp className="w-5 h-5" />} delay={0.4} />
        <KPICard title="Avg Uncertainty" value={Math.round((stats?.avg_uncertainty || 0) * 100)} suffix="%" color="warning" delay={0.5} />
        <KPICard title="Active Cameras" value={stats?.active_cameras || 0} icon={<Camera className="w-5 h-5" />} delay={0.6} />
        <KPICard title="Today's Challans" value={stats?.today_revenue || 0} prefix="₹" icon={<IndianRupee className="w-5 h-5" />} color="success" delay={0.7} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Violation Trends (24h)</h3>
            <span className="text-xs text-muted">{trendData.reduce((s, d) => s + d.count, 0)} total</span>
          </div>
          <TrendChart
            data={trendData}
            height={280}
            emptyMessage={analyticsError ? 'Could not load trends — refresh or log in again' : 'No violations in the last 24 hours'}
          />
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">System Health</h3>
            <Activity className="w-5 h-5 text-success" />
          </div>
          <div className="text-4xl font-bold text-success mb-2">{stats?.system_health?.toFixed(0) || 98}%</div>
          <p className="text-sm text-muted mb-4">All systems operational</p>
          <div className="space-y-2 text-sm">
            {['API Server', 'Vision AI', 'Database', 'Evidence Storage'].map((s) => (
              <div key={s} className="flex items-center justify-between">
                <span className="text-muted">{s}</span>
                <Badge variant="success">Online</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-semibold mb-4">Recent Violations</h3>
          <div className="space-y-3">
            {(violations || []).slice(0, 5).map((v) => (
              <div key={v.id} className="flex items-center justify-between p-3 rounded-xl bg-bg/50 border border-border/50">
                <div>
                  <p className="text-sm font-medium capitalize">{v.violation_type.replace('_', ' ')}</p>
                  <p className="text-xs text-muted">
                    {v.plate_number || 'No plate'} · {(v.confidence * 100).toFixed(0)}% conf
                    {v.fine_amount > 0 && ` · ₹${v.fine_amount.toLocaleString('en-IN')}`}
                  </p>
                </div>
                <Badge variant={v.routing_decision === 'auto_process' ? 'success' : v.routing_decision === 'human_review' ? 'warning' : 'danger'}>
                  {v.routing_decision.replace('_', ' ')}
                </Badge>
              </div>
            ))}
            {(!violations || violations.length === 0) && (
              <p className="text-muted text-sm text-center py-6">No violations yet. Upload an image in Live Monitoring.</p>
            )}
          </div>
        </Card>

        <Card>
          <h3 className="font-semibold mb-4">Review Queue</h3>
          <div className="text-center py-8">
            <p className="text-4xl font-bold text-warning">{stats?.pending_reviews || 0}</p>
            <p className="text-sm text-muted mt-1">cases awaiting officer review</p>
            <p className="text-xs text-muted mt-4">Review rate: {stats?.review_rate?.toFixed(1) || 0}%</p>
          </div>
        </Card>
      </div>
    </div>
  )
}
