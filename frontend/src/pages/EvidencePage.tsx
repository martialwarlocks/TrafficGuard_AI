import { useQuery } from '@tanstack/react-query'
import { Shield, Hash, Clock } from 'lucide-react'
import { Card, Badge } from '@/components/ui'
import { ConfidenceGauge } from '@/components/Gauge'
import { api } from '@/lib/api'

export function EvidencePage() {
  const { data: violations } = useQuery({ queryKey: ['violations'], queryFn: () => api.getViolations({ limit: '20' }) })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Evidence Viewer</h1>
        <p className="text-muted text-sm">All uploaded images are stored with chain of custody</p>
      </div>

      <div className="grid gap-4">
        {(violations || []).map((v) => (
          <EvidenceCard key={v.id} violationId={v.id} violation={v} />
        ))}
        {(!violations || violations.length === 0) && (
          <Card className="text-center py-12 text-muted">
            <p>No evidence yet.</p>
            <p className="text-xs mt-2">Upload an image in Live Monitoring to create evidence records.</p>
          </Card>
        )}
      </div>
    </div>
  )
}

function EvidenceCard({ violationId, violation }: { violationId: number; violation: import('@/lib/api').Violation }) {
  const { data: detail } = useQuery({
    queryKey: ['violation-detail', violationId],
    queryFn: () => api.getViolationDetail(violationId),
  })

  const img = detail?.image_urls?.annotated_url || detail?.image_urls?.original_url

  return (
    <Card className="grid lg:grid-cols-12 gap-6">
      <div className="lg:col-span-4">
        <div className="aspect-video bg-bg rounded-lg border border-border overflow-hidden mb-3">
          {img ? (
            <img src={img} alt={`Evidence ${violationId}`} className="w-full h-full object-contain" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted text-sm">Loading...</div>
          )}
        </div>
      </div>

      <div className="lg:col-span-5 space-y-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold capitalize">{violation.violation_type.replace('_', ' ')}</h3>
          <Badge variant={violation.status === 'approved' ? 'success' : 'warning'}>{violation.status}</Badge>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2"><Hash className="w-4 h-4 text-muted" /><span>#{violation.id}</span></div>
          <div className="flex items-center gap-2"><Clock className="w-4 h-4 text-muted" /><span>{new Date(violation.detected_at).toLocaleString()}</span></div>
          <div className="flex items-center gap-2"><Shield className="w-4 h-4 text-success" /><span className="text-success">Stored in MinIO</span></div>
        </div>
        {violation.explanation?.reasons && (
          <div className="text-sm text-muted">{violation.explanation.reasons[0]}</div>
        )}
      </div>

      <div className="lg:col-span-3 flex flex-col items-center justify-center gap-4">
        <ConfidenceGauge value={violation.confidence} label="Confidence" type="confidence" size={100} />
        <ConfidenceGauge value={violation.uncertainty} label="Uncertainty" type="uncertainty" size={100} />
        <div className="text-center">
          <p className="text-xs text-muted">Plate</p>
          <p className="font-mono font-bold">{detail?.ocr_result?.text || violation.plate_number || 'N/A'}</p>
        </div>
      </div>
    </Card>
  )
}
