import { useState, useRef, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Upload, Camera, Brain, ClipboardPaste, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react'
import { Card, Badge, Button } from '@/components/ui'
import { ConfidenceGauge, RadarChart } from '@/components/Gauge'
import { api, type AnalyzeResult } from '@/lib/api'
import { useAppStore } from '@/store'

export function MonitoringPage() {
  const [analysis, setAnalysis] = useState<AnalyzeResult | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()
  const addAlert = useAppStore((s) => s.addAlert)

  const { data: cameras } = useQuery({ queryKey: ['cameras'], queryFn: () => api.getCameras() })

  const handleUpload = useCallback(async (file: File) => {
    setAnalyzing(true)
    setError('')
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(URL.createObjectURL(file))

    try {
      const result = await api.analyzeImage(file)
      setAnalysis(result)
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
      queryClient.invalidateQueries({ queryKey: ['violations'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })

      if (result.routing_decision === 'human_review') {
        addAlert({
          title: 'Sent to Human Review',
          message: result.user_summary?.headline || 'Case queued for officer review',
          type: 'warning',
        })
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
      setAnalysis(null)
    } finally {
      setAnalyzing(false)
    }
  }, [previewUrl, queryClient, addAlert])

  const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items
    if (!items) return
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile()
        if (file) {
          e.preventDefault()
          await handleUpload(file)
          return
        }
      }
    }
  }, [handleUpload])

  const displayImage = analysis?.image_urls?.annotated || analysis?.image_urls?.original || previewUrl
  const summary = analysis?.user_summary

  return (
    <div className="space-y-4" onPaste={handlePaste}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Live Monitoring</h1>
          <p className="text-muted text-sm">Upload or paste an image — results appear in plain English</p>
        </div>
        <div className="flex gap-2">
          <input ref={fileRef} type="file" accept="image/*" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} />
          <Button variant="secondary" onClick={() => fileRef.current?.click()} disabled={analyzing}>
            <Upload className="w-4 h-4 mr-2" /> Upload
          </Button>
          <Button disabled={analyzing}>
            <ClipboardPaste className="w-4 h-4 mr-2" /> Paste (Ctrl+V)
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm">{error}</div>
      )}

      <div className="grid lg:grid-cols-12 gap-4">
        {/* Camera Grid */}
        <div className="lg:col-span-3 space-y-3 overflow-y-auto max-h-[calc(100vh-160px)]">
          <h3 className="text-sm font-semibold text-muted">Cameras</h3>
          {(cameras || []).map((cam) => (
            <div key={cam.id} className="rounded-lg bg-card border border-border p-3">
              <div className="aspect-video bg-bg rounded-md flex items-center justify-center mb-2 relative">
                <Camera className="w-8 h-8 text-muted" />
                <Badge variant={cam.status === 'online' ? 'success' : 'danger'} className="absolute top-2 right-2">
                  {cam.status}
                </Badge>
              </div>
              <p className="text-sm font-medium">{cam.name}</p>
              <p className="text-xs text-muted">{cam.location_name}</p>
            </div>
          ))}
        </div>

        {/* Main feed */}
        <div className="lg:col-span-6 space-y-4">
          <Card className="p-0 overflow-hidden">
            <div className="aspect-video bg-bg relative flex items-center justify-center">
              {analyzing && (
                <div className="absolute inset-0 bg-bg/80 flex items-center justify-center z-10">
                  <div className="text-center">
                    <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-sm text-muted">Analyzing image...</p>
                  </div>
                </div>
              )}
              {displayImage ? (
                <img src={displayImage} alt="Analysis" className="w-full h-full object-contain" />
              ) : (
                <div className="text-center text-muted p-8">
                  <Camera className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p className="font-medium">No image yet</p>
                  <p className="text-xs mt-2">Upload a photo or paste from clipboard (Ctrl+V / Cmd+V)</p>
                </div>
              )}
            </div>
          </Card>

          {/* User-friendly verdict */}
          {analysis && summary && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="border-primary/20">
                <div className="flex items-start gap-3 mb-4">
                  {analysis.routing_decision === 'auto_process' ? (
                    <CheckCircle className="w-6 h-6 text-success shrink-0 mt-0.5" />
                  ) : analysis.routing_decision === 'human_review' ? (
                    <AlertTriangle className="w-6 h-6 text-warning shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-6 h-6 text-muted shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h2 className="text-lg font-bold">
                      {summary.violation_label || summary.headline}
                    </h2>
                    <p className="text-sm text-muted mt-1">{summary.verdict.replace(/\*\*/g, '')}</p>
                    {analysis.traffic_signal?.state && analysis.traffic_signal.state !== 'unknown' && (
                      <p className="text-xs mt-2">
                        Traffic signal: <span className={analysis.traffic_signal.state === 'red' ? 'text-danger' : 'text-success'}>
                          {analysis.traffic_signal.state.toUpperCase()}
                        </span> ({(analysis.traffic_signal.confidence * 100).toFixed(0)}%)
                      </p>
                    )}
                  </div>
                </div>

                {summary.found_items.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-muted mb-2 uppercase tracking-wide">What we found</p>
                    <div className="flex flex-wrap gap-2">
                      {summary.found_items.map((item) => (
                        <span key={item.label} className="px-3 py-1.5 rounded-full bg-bg text-sm border border-border">
                          {item.count}× {item.label} <span className="text-muted">({(item.confidence * 100).toFixed(0)}%)</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.ocr_result?.text && (
                  <div className="mb-4 p-3 rounded-lg bg-bg">
                    <p className="text-xs text-muted">License plate</p>
                    <p className="font-mono font-bold text-lg">{analysis.ocr_result.text}</p>
                  </div>
                )}

                <div className="p-3 rounded-lg bg-bg border-l-2 border-primary mb-4">
                  <p className="text-xs text-muted mb-1">What happens next</p>
                  <p className="text-sm">{summary.next_step}</p>
                </div>

                <div className="flex items-center gap-3 flex-wrap">
                  <Badge variant={
                    analysis.routing_decision === 'auto_process' ? 'success'
                      : analysis.routing_decision === 'human_review' ? 'warning' : 'muted'
                  }>
                    {analysis.routing_decision.replace(/_/g, ' ').toUpperCase()}
                  </Badge>
                  <span className="text-xs text-muted">{analysis.processing_time_ms.toFixed(0)}ms</span>
                  {analysis.violation_id && analysis.routing_decision === 'human_review' && (
                    <Link to="/review">
                      <Button size="sm">
                        Open in Review Queue <ArrowRight className="w-3 h-3 ml-1" />
                      </Button>
                    </Link>
                  )}
                </div>
              </Card>
            </motion.div>
          )}
        </div>

        {/* AI Copilot */}
        <div className="lg:col-span-3 space-y-4">
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-5 h-5 text-primary" />
              <h3 className="font-semibold">AI Copilot</h3>
            </div>
            {analysis ? (
              <div className="space-y-4">
                <div className="flex justify-around">
                  <ConfidenceGauge value={analysis.confidence} label="Confidence" type="confidence" size={90} />
                  <ConfidenceGauge value={analysis.uncertainty} label="Uncertainty" type="uncertainty" size={90} />
                </div>
                <div>
                  <p className="text-xs text-muted mb-2">Why this decision?</p>
                  <div className="space-y-2">
                    {analysis.explanation.reasons.map((r, i) => (
                      <div key={i} className="p-2 rounded-lg bg-bg text-sm border-l-2 border-primary">{r}</div>
                    ))}
                  </div>
                </div>
                <RadarChart confidence={analysis.confidence} uncertainty={analysis.uncertainty} />
                <p className="text-xs text-muted">Image quality: {(analysis.quality_score * 100).toFixed(0)}%</p>
              </div>
            ) : (
              <p className="text-sm text-muted">
                Upload or paste an image. The copilot will explain the decision in plain language.
              </p>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
