import {
  Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'

interface TrendPoint {
  label: string
  count: number
  auto: number
  review: number
}

interface TrendChartProps {
  data: TrendPoint[]
  height?: number
  emptyMessage?: string
}

export function TrendChart({
  data,
  height = 280,
  emptyMessage = 'No violations in this period — analyze images in Live Monitoring',
}: TrendChartProps) {
  const hasData = data.some((d) => d.count > 0)

  return (
    <div className="w-full" style={{ height, minHeight: height, minWidth: 0 }}>
      {!hasData ? (
        <div className="h-full flex flex-col items-center justify-center text-center px-4">
          <p className="text-muted text-sm">{emptyMessage}</p>
          <p className="text-xs text-muted/70 mt-2">Chart shows violations as they are recorded</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height} minWidth={0}>
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="tgCount" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4F8CFF" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#4F8CFF" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} width={32} />
            <Tooltip
              contentStyle={{ background: '#121A2F', border: '1px solid #1E293B', borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: '#94A3B8' }}
            />
            <Area type="monotone" dataKey="count" stroke="#4F8CFF" strokeWidth={2} fill="url(#tgCount)" name="Total" />
            <Area type="monotone" dataKey="auto" stroke="#00C853" strokeWidth={1.5} fill="transparent" name="Auto" />
            <Area type="monotone" dataKey="review" stroke="#FFB300" strokeWidth={1.5} fill="transparent" name="Review" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
