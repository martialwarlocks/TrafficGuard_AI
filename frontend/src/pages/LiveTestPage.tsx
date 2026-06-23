import { useQueryClient } from '@tanstack/react-query'
import { Video } from 'lucide-react'
import { LiveWebcam } from '@/components/LiveWebcam'
import type { AnalyzeResult } from '@/lib/api'

export function LiveTestPage() {
  const queryClient = useQueryClient()

  const handleViolation = () => {
    queryClient.invalidateQueries({ queryKey: ['review-queue'] })
    queryClient.invalidateQueries({ queryKey: ['violations'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-2">
          <Video className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold">Live Webcam Test</h1>
        </div>
        <p className="text-muted text-sm mt-1">
          Real-time traffic violation detection using your webcam. Point at a traffic scene or show violation photos on another screen.
        </p>
      </div>

      <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 text-sm">
        <strong>Demo tip:</strong> Hold your red-light violation photo up to the webcam, or point the camera at a busy intersection.
        The AI analyzes every {2.5}s and flags violations with confidence scores and explainability.
      </div>

      <LiveWebcam intervalMs={2500} onViolation={handleViolation as (r: AnalyzeResult) => void} />
    </div>
  )
}
