import { motion } from 'framer-motion'

interface GaugeProps {
  value: number
  label: string
  type: 'confidence' | 'uncertainty'
  size?: number
}

export function ConfidenceGauge({ value, label, type, size = 120 }: GaugeProps) {
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value * circumference)
  const color = type === 'confidence'
    ? value >= 0.85 ? '#00C853' : value >= 0.60 ? '#FFB300' : '#FF5252'
    : value <= 0.20 ? '#00C853' : value <= 0.40 ? '#FFB300' : '#FF5252'

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="#1E293B" strokeWidth="8"
          />
          <motion.circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold" style={{ color }}>{(value * 100).toFixed(0)}%</span>
        </div>
      </div>
      <span className="text-xs text-muted mt-2">{label}</span>
    </div>
  )
}

export function RadarChart({ confidence, uncertainty }: { confidence: number; uncertainty: number }) {
  const points = [
    { label: 'Model', value: confidence },
    { label: 'Quality', value: confidence * 0.9 },
    { label: 'OCR', value: confidence * 0.85 },
    { label: 'Stability', value: 1 - uncertainty },
    { label: 'Evidence', value: (confidence + (1 - uncertainty)) / 2 },
  ]

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted text-center mb-3">Confidence vs Uncertainty Radar</p>
      {points.map((p) => (
        <div key={p.label} className="flex items-center gap-2">
          <span className="text-xs text-muted w-16">{p.label}</span>
          <div className="flex-1 h-2 bg-bg rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-primary"
              initial={{ width: 0 }}
              animate={{ width: `${p.value * 100}%` }}
              transition={{ duration: 0.8, delay: 0.1 }}
            />
          </div>
          <span className="text-xs text-text w-10">{(p.value * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  )
}
