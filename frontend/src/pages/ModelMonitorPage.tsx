import { useQuery } from '@tanstack/react-query'
import { Card, Badge } from '@/components/ui'
import { KPICard } from '@/components/KPICard'
import { api } from '@/lib/api'
import { Cpu, Zap, Activity, AlertTriangle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export function ModelMonitorPage() {
  const { data: metrics } = useQuery({ queryKey: ['model-metrics'], queryFn: () => api.getModelMetrics(), refetchInterval: 30000 })

  const perfData = [
    { metric: 'Precision', value: (metrics?.precision || 0) * 100 },
    { metric: 'Recall', value: (metrics?.recall || 0) * 100 },
    { metric: 'mAP50', value: (metrics?.map50 || 0) * 100 },
    { metric: 'mAP50-95', value: (metrics?.map50_95 || 0) * 100 },
    { metric: 'F1', value: (metrics?.f1_score || 0) * 100 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Model Monitoring</h1>
        <p className="text-muted text-sm">YOLOv8s performance, drift alerts, and retraining status</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {perfData.map((m, i) => (
          <KPICard key={m.metric} title={m.metric} value={Math.round(m.value)} suffix="%" delay={i * 0.1} />
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <KPICard title="Latency" value={Math.round(metrics?.latency_ms || 45)} suffix="ms" icon={<Zap className="w-5 h-5" />} />
        <KPICard title="FPS" value={Math.round(metrics?.fps || 22)} icon={<Activity className="w-5 h-5" />} color="success" />
        <KPICard title="GPU Utilization" value={Math.round(metrics?.gpu_utilization || 68)} suffix="%" icon={<Cpu className="w-5 h-5" />} color="warning" />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-semibold mb-4">Model Performance</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={perfData}>
              <XAxis dataKey="metric" stroke="#94A3B8" fontSize={11} />
              <YAxis stroke="#94A3B8" domain={[0, 100]} fontSize={11} />
              <Tooltip contentStyle={{ background: '#121A2F', border: '1px solid #1E293B' }} />
              <Line type="monotone" dataKey="value" stroke="#4F8CFF" strokeWidth={2} dot={{ fill: '#4F8CFF' }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="font-semibold mb-4">Confidence vs Uncertainty</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted">Avg Confidence</span>
                <span>{((metrics?.avg_confidence || 0.78) * 100).toFixed(1)}%</span>
              </div>
              <div className="h-3 bg-bg rounded-full"><div className="h-full bg-success rounded-full" style={{ width: `${(metrics?.avg_confidence || 0.78) * 100}%` }} /></div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted">Avg Uncertainty</span>
                <span>{((metrics?.avg_uncertainty || 0.22) * 100).toFixed(1)}%</span>
              </div>
              <div className="h-3 bg-bg rounded-full"><div className="h-full bg-warning rounded-full" style={{ width: `${(metrics?.avg_uncertainty || 0.22) * 100}%` }} /></div>
            </div>
            <div className="pt-4">
              <p className="text-sm text-muted mb-2">Retraining Status</p>
              <Badge variant={metrics?.retraining_status === 'idle' ? 'success' : 'warning'}>
                {metrics?.retraining_status || 'idle'}
              </Badge>
            </div>
          </div>
        </Card>
      </div>

      {(metrics?.drift_alerts || []).length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-warning" />
            <h3 className="font-semibold">Drift Alerts</h3>
          </div>
          <div className="space-y-2">
            {metrics!.drift_alerts.map((alert, i) => (
              <div key={i} className="p-3 rounded-lg bg-bg flex items-center justify-between">
                <span className="text-sm">{alert.message}</span>
                <Badge variant="warning">{alert.severity}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
