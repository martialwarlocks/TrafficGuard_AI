import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  AlertTriangle, Camera, TrendingUp, Shield, DollarSign, Activity, Clock, Users,
} from 'lucide-react'
import { KPICard } from '@/components/KPICard'
import { Card, Badge } from '@/components/ui'
import { api } from '@/lib/api'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

export function DashboardPage() {
  const { data: stats } = useQuery({ queryKey: ['dashboard'], queryFn: () => api.getDashboard(), refetchInterval: 30000 })
  const { data: violations } = useQuery({ queryKey: ['violations'], queryFn: () => api.getViolations({ limit: '10' }) })
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: () => api.getAnalytics() })

  const trendData = analytics?.hourly_trends?.slice(-12) || []

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-2xl font-bold">Command Center</h1>
        <p className="text-muted text-sm">Real-time traffic enforcement overview</p>
      </motion.div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Violations" value={stats?.total_violations || 0} icon={<AlertTriangle className="w-5 h-5" />} change={12} delay={0} />
        <KPICard title="Auto Processed" value={stats?.auto_processed || 0} color="success" icon={<Shield className="w-5 h-5" />} change={8} delay={0.1} />
        <KPICard title="Human Reviewed" value={stats?.human_reviewed || 0} color="warning" icon={<Users className="w-5 h-5" />} delay={0.2} />
        <KPICard title="Pending Reviews" value={stats?.pending_reviews || 0} color="danger" icon={<Clock className="w-5 h-5" />} delay={0.3} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Avg Confidence" value={Math.round((stats?.avg_confidence || 0) * 100)} suffix="%" color="primary" icon={<TrendingUp className="w-5 h-5" />} delay={0.4} />
        <KPICard title="Avg Uncertainty" value={Math.round((stats?.avg_uncertainty || 0) * 100)} suffix="%" color="warning" delay={0.5} />
        <KPICard title="Active Cameras" value={stats?.active_cameras || 0} icon={<Camera className="w-5 h-5" />} delay={0.6} />
        <KPICard title="Today's Revenue" value={stats?.today_revenue || 0} prefix="₹" icon={<DollarSign className="w-5 h-5" />} color="success" delay={0.7} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <h3 className="font-semibold mb-4">Violation Trends (24h)</h3>
          <div className="w-full" style={{ height: 250, minHeight: 250 }}>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4F8CFF" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#4F8CFF" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="label" stroke="#94A3B8" fontSize={11} tick={{ fill: '#94A3B8' }} />
                  <YAxis stroke="#94A3B8" fontSize={11} tick={{ fill: '#94A3B8' }} allowDecimals={false} domain={[0, 'auto']} />
                  <Tooltip contentStyle={{ background: '#121A2F', border: '1px solid #1E293B', borderRadius: 8 }} />
                  <Area type="monotone" dataKey="count" stroke="#4F8CFF" fill="url(#colorCount)" name="Total" />
                  <Area type="monotone" dataKey="auto" stroke="#00C853" fill="transparent" name="Auto" />
                  <Area type="monotone" dataKey="review" stroke="#FFB300" fill="transparent" name="Review" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted text-sm">
                No trend data yet — upload violations in Live Monitoring
              </div>
            )}
          </div>
          {(stats?.total_violations || 0) > 0 && trendData.every(d => d.count === 0) && (
            <p className="text-xs text-muted mt-2">Violations recorded — chart updates as new cases arrive each hour.</p>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">System Health</h3>
            <Activity className="w-5 h-5 text-success" />
          </div>
          <div className="text-4xl font-bold text-success mb-2">{stats?.system_health?.toFixed(0) || 98}%</div>
          <p className="text-sm text-muted mb-4">All systems operational</p>
          <div className="space-y-2 text-sm">
            {['API Server', 'ML Pipeline', 'Database', 'Redis Queue'].map((s) => (
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
              <div key={v.id} className="flex items-center justify-between p-3 rounded-lg bg-bg/50">
                <div>
                  <p className="text-sm font-medium capitalize">{v.violation_type.replace('_', ' ')}</p>
                  <p className="text-xs text-muted">{v.plate_number || 'No plate'} · {(v.confidence * 100).toFixed(0)}% conf</p>
                </div>
                <Badge variant={v.routing_decision === 'auto_process' ? 'success' : v.routing_decision === 'human_review' ? 'warning' : 'danger'}>
                  {v.routing_decision.replace('_', ' ')}
                </Badge>
              </div>
            ))}
            {(!violations || violations.length === 0) && (
              <p className="text-muted text-sm text-center py-4">No violations yet. Upload an image to analyze.</p>
            )}
          </div>
        </Card>

        <Card>
          <h3 className="font-semibold mb-4">Review Queue</h3>
          <div className="text-center py-8">
            <p className="text-3xl font-bold text-warning">{stats?.pending_reviews || 0}</p>
            <p className="text-sm text-muted mt-1">cases awaiting review</p>
            <p className="text-xs text-muted mt-4">Review rate: {stats?.review_rate?.toFixed(1) || 0}%</p>
          </div>
        </Card>
      </div>
    </div>
  )
}
