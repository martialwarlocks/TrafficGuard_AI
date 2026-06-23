import { useRef, useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Video, VideoOff, Scan, AlertTriangle } from 'lucide-react'
import { Card, Badge, Button } from '@/components/ui'
import { ConfidenceGauge } from '@/components/Gauge'
import { EnforcementCard } from '@/components/EnforcementCard'
import { api, type AnalyzeResult } from '@/lib/api'
import { useAppStore } from '@/store'

interface LiveHit {
  id: string
  time: Date
  result: AnalyzeResult
}

interface LiveWebcamProps {
  intervalMs?: number
  onViolation?: (result: AnalyzeResult) => void
}

export function LiveWebcam({ intervalMs = 2500, onViolation }: LiveWebcamProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<number | null>(null)

  const [active, setActive] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState('')
  const [latest, setLatest] = useState<AnalyzeResult | null>(null)
  const [annotatedUrl, setAnnotatedUrl] = useState<string | null>(null)
  const [hits, setHits] = useState<LiveHit[]>([])
  const [frameCount, setFrameCount] = useState(0)
  const addAlert = useAppStore((s) => s.addAlert)

  const stopCamera = useCallback(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setActive(false)
    setScanning(false)
  }, [])

  const captureAndAnalyze = useCallback(async () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || video.readyState < 2 || scanning) return

    setScanning(true)
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0)

    canvas.toBlob(async (blob) => {
      if (!blob) {
        setScanning(false)
        return
      }
      try {
        const file = new File([blob], `live-${Date.now()}.jpg`, { type: 'image/jpeg' })
        const result = await api.analyzeImage(file, undefined, true)
        setLatest(result)
        setFrameCount((c) => c + 1)

        if (result.annotated_image_b64) {
          setAnnotatedUrl(`data:image/jpeg;base64,${result.annotated_image_b64}`)
        }

        const isViolation = result.violation_type && result.routing_decision !== 'discard'
        if (isViolation) {
          const hit: LiveHit = { id: crypto.randomUUID(), time: new Date(), result }
          setHits((prev) => [hit, ...prev].slice(0, 10))
          onViolation?.(result)
          addAlert({
            title: result.user_summary?.headline || 'Violation detected',
            message: result.user_summary?.verdict?.slice(0, 80) || '',
            type: result.routing_decision === 'auto_process' ? 'danger' : 'warning',
          })
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Analysis failed')
      } finally {
        setScanning(false)
      }
    }, 'image/jpeg', 0.85)
  }, [scanning, onViolation, addAlert])

  const startCamera = async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setActive(true)
      timerRef.current = window.setInterval(captureAndAnalyze, intervalMs)
      captureAndAnalyze()
    } catch {
      setError('Camera access denied. Allow webcam permission and try again.')
    }
  }

  useEffect(() => () => stopCamera(), [stopCamera])

  const summary = latest?.user_summary
  const displaySrc = annotatedUrl || (active ? undefined : null)

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm">{error}</div>
      )}

      <div className="grid lg:grid-cols-3 gap-4">
        {/* Camera feed */}
        <Card className="lg:col-span-2 p-0 overflow-hidden">
          <div className="relative aspect-video bg-black">
            <video
              ref={videoRef}
              className={`w-full h-full object-contain ${displaySrc ? 'hidden' : ''}`}
              playsInline
              muted
            />
            {displaySrc && (
              <img src={displaySrc} alt="Annotated" className="w-full h-full object-contain" />
            )}
            {!active && !displaySrc && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted">
                <Video className="w-16 h-16 mb-4 opacity-30" />
                <p>Camera off — click Start Live Test</p>
              </div>
            )}

            {/* Live indicators */}
            {active && (
              <div className="absolute top-3 left-3 flex items-center gap-2">
                <span className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-danger/90 text-white text-xs font-medium">
                  <span className="w-2 h-2 rounded-full bg-white animate-pulse" /> LIVE
                </span>
                {scanning && (
                  <span className="px-2 py-1 rounded-full bg-primary/90 text-white text-xs flex items-center gap-1">
                    <Scan className="w-3 h-3 animate-spin" /> Analyzing
                  </span>
                )}
              </div>
            )}

            {latest?.traffic_signal?.state && latest.traffic_signal.state !== 'unknown' && (
              <div className="absolute top-3 right-3">
                <Badge variant={latest.traffic_signal.state === 'red' ? 'danger' : 'success'}>
                  SIGNAL: {latest.traffic_signal.state.toUpperCase()}
                </Badge>
              </div>
            )}

            {summary && active && (
              <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/90 to-transparent">
                <p className="font-semibold text-sm">{summary.violation_label || summary.headline}</p>
                <p className="text-xs text-gray-300 truncate">{summary.verdict}</p>
              </div>
            )}
          </div>

          <canvas ref={canvasRef} className="hidden" />

          <div className="p-4 flex items-center justify-between border-t border-border">
            <div className="text-xs text-muted">
              {active ? `${frameCount} frames analyzed · every ${intervalMs / 1000}s` : 'Point camera at traffic scene'}
            </div>
            <div className="flex gap-2">
              {!active ? (
                <Button onClick={startCamera}>
                  <Video className="w-4 h-4 mr-2" /> Start Live Test
                </Button>
              ) : (
                <>
                  <Button variant="secondary" onClick={captureAndAnalyze} disabled={scanning}>
                    <Scan className="w-4 h-4 mr-2" /> Scan Now
                  </Button>
                  <Button variant="danger" onClick={stopCamera}>
                    <VideoOff className="w-4 h-4 mr-2" /> Stop
                  </Button>
                </>
              )}
            </div>
          </div>
        </Card>

        {/* Side panel */}
        <div className="space-y-4">
          {latest ? (
            <Card>
              <h3 className="font-semibold mb-3 text-sm">Latest Scan</h3>
              <EnforcementCard analysis={latest} />
              <div className="flex justify-around mb-3 mt-3">
                <ConfidenceGauge value={latest.confidence} label="Confidence" type="confidence" size={70} />
                <ConfidenceGauge value={latest.uncertainty} label="Uncertainty" type="uncertainty" size={70} />
              </div>
              <Badge variant={
                latest.routing_decision === 'auto_process' ? 'success'
                  : latest.routing_decision === 'human_review' ? 'warning' : 'muted'
              }>
                {latest.routing_decision.replace(/_/g, ' ').toUpperCase()}
              </Badge>
              <p className="text-xs text-muted mt-2">{latest.processing_time_ms.toFixed(0)}ms</p>
            </Card>
          ) : (
            <Card>
              <p className="text-sm text-muted">Start the camera to begin real-time violation detection.</p>
            </Card>
          )}

          <Card>
            <h3 className="font-semibold mb-3 text-sm">Violation Log</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              <AnimatePresence>
                {hits.map((h) => (
                  <motion.div
                    key={h.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-2 rounded-lg bg-bg border border-border text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-warning shrink-0" />
                      <span className="font-medium capitalize truncate">
                        {h.result.user_summary?.violation_label || h.result.violation_type?.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-muted mt-1">{h.time.toLocaleTimeString()}</p>
                  </motion.div>
                ))}
              </AnimatePresence>
              {hits.length === 0 && (
                <p className="text-xs text-muted text-center py-4">No violations detected yet</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
