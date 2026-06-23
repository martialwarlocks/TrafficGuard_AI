import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Badge } from '@/components/ui'
import { TrendChart } from '@/components/TrendChart'
import { api } from '@/lib/api'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area,
} from 'recharts'

const COLORS = ['#4F8CFF', '#00C853', '#FFB300', '#FF5252', '#94A3B8', '#A855F7']

export function AnalyticsPage() {
  const [period, setPeriod] = useState<'hourly' | 'daily' | 'monthly'>('daily')
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: () => api.getAnalytics() })
  const { data: heatmap } = useQuery({ queryKey: ['heatmap'], queryFn: () => api.getHeatmap() })

  const trendData = period === 'hourly' ? analytics?.hourly_trends
    : period === 'monthly' ? analytics?.monthly_trends
    : analytics?.daily_trends

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Smart City Analytics</h1>
          <p className="text-muted text-sm">Violation patterns, officer productivity, and model drift</p>
        </div>
        <div className="flex gap-2">
          {(['hourly', 'daily', 'monthly'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 rounded-lg text-sm capitalize ${period === p ? 'bg-primary text-white' : 'bg-card text-muted'}`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <Card>
        <h3 className="font-semibold mb-4">Violation Trends</h3>
        <TrendChart
          data={trendData || []}
          height={300}
          emptyMessage="No data for this period — violations appear here after analysis"
        />
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-semibold mb-4">Violation Categories</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={analytics?.violation_categories || []} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={80}
                label={(props) => `${props.name}: ${props.value}`}>
                {(analytics?.violation_categories || []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#121A2F', border: '1px solid #1E293B' }} />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="font-semibold mb-4">Officer Productivity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={analytics?.officer_productivity || []}>
              <XAxis dataKey="officer" stroke="#94A3B8" fontSize={10} />
              <YAxis stroke="#94A3B8" fontSize={11} />
              <Tooltip contentStyle={{ background: '#121A2F', border: '1px solid #1E293B' }} />
              <Bar dataKey="reviews" fill="#4F8CFF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-semibold mb-4">Confidence Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={analytics?.confidence_distribution || []}>
              <XAxis dataKey="bucket" stroke="#94A3B8" fontSize={11} />
              <YAxis stroke="#94A3B8" fontSize={11} />
              <Bar dataKey="count" fill="#00C853" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="font-semibold mb-4">Uncertainty Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={analytics?.uncertainty_distribution || []}>
              <XAxis dataKey="bucket" stroke="#94A3B8" fontSize={11} />
              <YAxis stroke="#94A3B8" fontSize={11} />
              <Bar dataKey="count" fill="#FFB300" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Model Drift Trends</h3>
          <Badge variant="success">Review Accuracy: {((analytics?.review_accuracy || 0.94) * 100).toFixed(0)}%</Badge>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={analytics?.model_drift || []}>
            <XAxis dataKey="date" stroke="#94A3B8" fontSize={10} />
            <YAxis stroke="#94A3B8" fontSize={11} />
            <Tooltip contentStyle={{ background: '#121A2F', border: '1px solid #1E293B' }} />
            <Line type="monotone" dataKey="drift" stroke="#FF5252" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card>
        <h3 className="font-semibold mb-4">Violation Hotspots ({heatmap?.length || 0} points)</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {(heatmap || []).slice(0, 8).map((p, i) => (
            <div key={i} className="p-3 rounded-lg bg-bg text-sm">
              <p className="font-medium">{p.violation_count} violations</p>
              <p className="text-xs text-muted">{p.latitude.toFixed(3)}, {p.longitude.toFixed(3)}</p>
              <div className="mt-2 h-1.5 bg-border rounded-full">
                <div className="h-full rounded-full bg-danger" style={{ width: `${p.intensity * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
