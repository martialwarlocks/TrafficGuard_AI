import { useQuery } from '@tanstack/react-query'
import { Card, Badge } from '@/components/ui'
import { api } from '@/lib/api'
import { MapPin, Camera, AlertTriangle } from 'lucide-react'

export function DigitalTwinPage() {
  const { data: cameras } = useQuery({ queryKey: ['cameras'], queryFn: () => api.getCameras() })
  const { data: heatmap } = useQuery({ queryKey: ['heatmap'], queryFn: () => api.getHeatmap() })

  const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Digital Twin</h1>
        <p className="text-muted text-sm">City-wide traffic intelligence and violation density</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-3">
          <Camera className="w-8 h-8 text-primary" />
          <div><p className="text-2xl font-bold">{cameras?.length || 0}</p><p className="text-xs text-muted">Cameras</p></div>
        </Card>
        <Card className="flex items-center gap-3">
          <AlertTriangle className="w-8 h-8 text-danger" />
          <div><p className="text-2xl font-bold">{heatmap?.length || 0}</p><p className="text-xs text-muted">Hotspots</p></div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-success" />
          <div><p className="text-2xl font-bold">{cameras?.filter(c => c.status === 'online').length || 0}</p><p className="text-xs text-muted">Online</p></div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-warning" />
          <div><p className="text-2xl font-bold">72</p><p className="text-xs text-muted">Safety Score</p></div>
        </Card>
      </div>

      <Card className="relative h-[500px] overflow-hidden">
        {mapboxToken && mapboxToken !== 'your_mapbox_token_here' ? (
          <div id="mapbox-container" className="w-full h-full" />
        ) : (
          <div className="w-full h-full bg-bg relative">
            {/* Fallback city map visualization */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_40%,rgba(79,140,255,0.1)_0%,transparent_50%),radial-gradient(circle_at_70%_60%,rgba(255,82,82,0.1)_0%,transparent_50%)]" />
            <svg className="w-full h-full" viewBox="0 0 800 500">
              {/* Roads */}
              <line x1="0" y1="250" x2="800" y2="250" stroke="#1E293B" strokeWidth="3" />
              <line x1="400" y1="0" x2="400" y2="500" stroke="#1E293B" strokeWidth="3" />
              <line x1="100" y1="100" x2="700" y2="400" stroke="#1E293B" strokeWidth="2" />
              <line x1="700" y1="100" x2="100" y2="400" stroke="#1E293B" strokeWidth="2" />

              {/* Camera markers */}
              {(cameras || []).map((cam, i) => {
                const x = 150 + (i * 150) % 600
                const y = 120 + (i * 80) % 300
                const color = cam.status === 'online' ? '#00C853' : '#FF5252'
                return (
                  <g key={cam.id}>
                    <circle cx={x} cy={y} r="20" fill={color} opacity="0.2" />
                    <circle cx={x} cy={y} r="8" fill={color} />
                    <text x={x} y={y + 25} fill="#94A3B8" fontSize="10" textAnchor="middle">{cam.name.split(' ')[0]}</text>
                  </g>
                )
              })}

              {/* Hotspots */}
              {(heatmap || []).slice(0, 5).map((p, i) => {
                const x = 200 + i * 120
                const y = 180 + (i % 3) * 60
                const r = 15 + p.intensity * 25
                const color = p.intensity > 0.7 ? '#FF5252' : p.intensity > 0.4 ? '#FFB300' : '#00C853'
                return (
                  <circle key={i} cx={x} cy={y} r={r} fill={color} opacity="0.3">
                    <animate attributeName="r" values={`${r};${r + 5};${r}`} dur="3s" repeatCount="indefinite" />
                  </circle>
                )
              })}
            </svg>
            <div className="absolute bottom-4 left-4 glass rounded-lg p-3 text-xs">
              <p className="text-muted mb-2">Set VITE_MAPBOX_TOKEN for full Mapbox view</p>
              <div className="flex gap-3">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-success" /> Low</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-warning" /> Medium</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-danger" /> High</span>
              </div>
            </div>
          </div>
        )}
      </Card>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3">
        {(cameras || []).map((cam) => (
          <Card key={cam.id} className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-4 h-4 text-primary" />
              <span className="font-medium text-sm">{cam.name}</span>
            </div>
            <p className="text-xs text-muted">{cam.location_name}</p>
            <Badge variant={cam.status === 'online' ? 'success' : 'danger'} className="mt-2">{cam.status}</Badge>
          </Card>
        ))}
      </div>
    </div>
  )
}
