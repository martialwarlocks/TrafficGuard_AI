import { motion, useSpring, useTransform } from 'framer-motion'
import { useEffect } from 'react'
import { cn } from '@/lib/utils'

interface KPICardProps {
  title: string
  value: number
  suffix?: string
  prefix?: string
  change?: number
  icon?: React.ReactNode
  color?: 'primary' | 'success' | 'warning' | 'danger'
  delay?: number
}

export function KPICard({ title, value, suffix = '', prefix = '', change, icon, color = 'primary', delay = 0 }: KPICardProps) {
  const spring = useSpring(0, { stiffness: 50, damping: 20 })
  const display = useTransform(spring, (v) => `${prefix}${Math.round(v).toLocaleString()}${suffix}`)

  useEffect(() => {
    spring.set(value)
  }, [value, spring])

  const colors = {
    primary: 'from-primary/20 to-transparent border-primary/20',
    success: 'from-success/20 to-transparent border-success/20',
    warning: 'from-warning/20 to-transparent border-warning/20',
    danger: 'from-danger/20 to-transparent border-danger/20',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
      className={cn(
        'rounded-xl bg-card border p-5 bg-gradient-to-br',
        colors[color]
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted mb-1">{title}</p>
          <motion.p className="text-2xl font-bold text-text">{display}</motion.p>
          {change !== undefined && (
            <p className={cn('text-xs mt-1', change >= 0 ? 'text-success' : 'text-danger')}>
              {change >= 0 ? '↑' : '↓'} {Math.abs(change)}% vs yesterday
            </p>
          )}
        </div>
        {icon && <div className="text-primary opacity-60">{icon}</div>}
      </div>
    </motion.div>
  )
}
