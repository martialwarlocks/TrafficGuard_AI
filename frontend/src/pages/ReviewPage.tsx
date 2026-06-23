import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Check, X, ArrowUp, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, Badge, Button } from '@/components/ui'
import { ConfidenceGauge } from '@/components/Gauge'
import { api, type Violation } from '@/lib/api'

export function ReviewPage() {
  const queryClient = useQueryClient()
  const [selected, setSelected] = useState<Violation | null>(null)
  const [notes, setNotes] = useState('')

  const { data: queue, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['review-queue'],
    queryFn: () => api.getReviewQueue(),
    refetchInterval: 5000,
  })

  const pendingCount = (queue || []).filter((v) =>
    ['pending', 'human_review', 'escalated'].includes(v.status)
  ).length

  const isActionable = (v: Violation) =>
    ['pending', 'human_review', 'escalated'].includes(v.status)

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['violation-detail', selected?.id],
    queryFn: () => api.getViolationDetail(selected!.id),
    enabled: !!selected?.id,
  })

  const reviewMutation = useMutation({
    mutationFn: (data: { violation_id: number; action: string; notes?: string }) => api.submitReview(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setSelected(null)
      setNotes('')
    },
  })

  const handleAction = (action: string) => {
    if (!selected) return
    reviewMutation.mutate({ violation_id: selected.id, action, notes })
  }

  const images = detail?.image_urls

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Human Review</h1>
        <p className="text-muted text-sm">Review cases flagged from Live Monitoring and borderline detections</p>
      </div>

      <div className="grid lg:grid-cols-12 gap-4">
        <div className="lg:col-span-3 space-y-2 max-h-[calc(100vh-180px)] overflow-y-auto">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-warning" />
            <span className="text-sm font-semibold">
              {pendingCount} pending · {(queue || []).length} total
            </span>
          </div>
          {isLoading && <p className="text-muted text-sm">Loading queue...</p>}
          {isError && (
            <div className="p-3 rounded-lg bg-danger/10 border border-danger/30 text-sm">
              <p className="text-danger">{error instanceof Error ? error.message : 'Failed to load queue'}</p>
              <button onClick={() => refetch()} className="text-primary text-xs mt-2 hover:underline">Retry</button>
            </div>
          )}
          {(queue || []).map((v) => (
            <motion.div
              key={v.id}
              whileHover={{ scale: 1.01 }}
              onClick={() => setSelected(v)}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selected?.id === v.id ? 'border-primary bg-primary/10' : 'border-border bg-card hover:border-primary/30'
              }`}
            >
              <div className="flex justify-between items-start gap-2">
                <p className="text-sm font-medium capitalize">{v.violation_type.replace('_', ' ')}</p>
                <Badge variant={isActionable(v) ? 'warning' : v.status === 'approved' ? 'success' : 'muted'}>
                  {isActionable(v) ? 'Review' : v.status}
                </Badge>
              </div>
              <p className="text-xs text-muted mt-1">{v.plate_number || 'No plate detected'}</p>
              {v.fine_amount > 0 && (
                <p className="text-xs text-danger font-medium">₹{v.fine_amount.toLocaleString('en-IN')}</p>
              )}
              <p className="text-xs text-muted">{(v.confidence * 100).toFixed(0)}% conf · {new Date(v.detected_at).toLocaleString()}</p>
            </motion.div>
          ))}
          {queue?.length === 0 && !isLoading && !isError && (
            <div className="text-center py-8 text-muted text-sm space-y-2">
              <p className="font-medium text-text">No flagged cases yet</p>
              <p className="text-xs">Upload an image in <Link to="/monitoring" className="text-primary hover:underline">Live Monitoring</Link> — medium-confidence detections appear here.</p>
            </div>
          )}
        </div>

        <div className="lg:col-span-6">
          {selected ? (
            <Card>
              {detailLoading ? (
                <p className="text-muted text-center py-12">Loading evidence...</p>
              ) : (
                <>
                  <div className="grid md:grid-cols-3 gap-4 mb-6">
                    {[
                      { label: 'Original', url: images?.original_url },
                      { label: 'Enhanced', url: images?.enhanced_url },
                      { label: 'Annotated', url: images?.annotated_url },
                    ].map(({ label, url }) => (
                      <div key={label}>
                        <p className="text-xs text-muted mb-2">{label}</p>
                        <div className="aspect-video bg-bg rounded-lg border border-border overflow-hidden">
                          {url ? (
                            <img src={url} alt={label} className="w-full h-full object-contain" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-xs text-muted">Not available</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <div>
                      <h3 className="font-semibold mb-3">Case Summary</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between"><span className="text-muted">Type</span><span className="capitalize">{selected.violation_type.replace('_', ' ')}</span></div>
                        <div className="flex justify-between"><span className="text-muted">Plate</span><span>{detail?.ocr_result?.text || selected.plate_number || 'N/A'}</span></div>
                        <div className="flex justify-between"><span className="text-muted">Vehicle</span><span className="capitalize">{selected.vehicle_type || 'Unknown'}</span></div>
                        {selected.fine_amount > 0 && (
                          <>
                            <div className="flex justify-between"><span className="text-muted">Challan</span><span className="font-bold text-danger">₹{selected.fine_amount.toLocaleString('en-IN')}</span></div>
                            <div className="flex justify-between"><span className="text-muted">MV Act</span><span className="text-xs text-right max-w-[60%]">{(selected.explanation as {legal_section?: string})?.legal_section || 'Section per violation type'}</span></div>
                          </>
                        )}
                        <div className="flex justify-between"><span className="text-muted">Status</span><Badge variant="warning">{selected.status}</Badge></div>
                      </div>
                      {detail?.detection_data && detail.detection_data.length > 0 && (
                        <div className="mt-4">
                          <p className="text-xs text-muted mb-2">Objects detected</p>
                          <div className="flex flex-wrap gap-1">
                            {detail.detection_data.map((d, i) => (
                              <span key={i} className="text-xs px-2 py-1 rounded bg-bg capitalize">
                                {d.class_name.replace('_', ' ')} ({(d.confidence * 100).toFixed(0)}%)
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center justify-around">
                      <ConfidenceGauge value={selected.confidence} label="Confidence" type="confidence" />
                      <ConfidenceGauge value={selected.uncertainty} label="Uncertainty" type="uncertainty" />
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Why flagged for review</h3>
                    <div className="grid md:grid-cols-2 gap-2">
                      {(selected.explanation?.reasons || ['Borderline confidence — officer verification needed']).map((r, i) => (
                        <div key={i} className="p-3 rounded-lg bg-bg border-l-2 border-warning text-sm">{r}</div>
                      ))}
                    </div>
                  </div>

                  <textarea
                    className="w-full p-3 rounded-lg bg-bg border border-border text-sm mb-4 resize-none"
                    rows={2}
                    placeholder="Officer notes..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />

                  <div className="flex gap-3">
                    {isActionable(selected) ? (
                      <>
                        <Button variant="success" onClick={() => handleAction('approve')} disabled={reviewMutation.isPending}>
                          <Check className="w-4 h-4 mr-2" /> Approve Violation
                        </Button>
                        <Button variant="danger" onClick={() => handleAction('reject')} disabled={reviewMutation.isPending}>
                          <X className="w-4 h-4 mr-2" /> Reject — No Violation
                        </Button>
                        <Button variant="secondary" onClick={() => handleAction('escalate')} disabled={reviewMutation.isPending}>
                          <ArrowUp className="w-4 h-4 mr-2" /> Escalate
                        </Button>
                      </>
                    ) : (
                      <p className="text-sm text-muted">
                        This case was already <span className="capitalize font-medium text-text">{selected.status}</span>.
                        Upload a new image in Live Monitoring to create pending cases.
                      </p>
                    )}
                  </div>
                </>
              )}
            </Card>
          ) : (
            <Card className="flex items-center justify-center h-96">
              <p className="text-muted">Select a case from the review queue</p>
            </Card>
          )}
        </div>

        <div className="lg:col-span-3">
          <Card>
            <h3 className="font-semibold mb-4">Routing Rationale</h3>
            {selected ? (
              <div className="space-y-4 text-sm">
                <Badge variant="warning">Human Review Required</Badge>
                <p className="text-muted">{selected.routing_rationale || 'Medium confidence detection flagged for officer review.'}</p>
                <div className="p-3 rounded-lg bg-bg text-xs text-muted space-y-1">
                  <p>≥85% confidence → Auto-process</p>
                  <p>60–84% confidence → Human review</p>
                  <p>&lt;60% confidence → Discard</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted">Select a case to view routing details.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
