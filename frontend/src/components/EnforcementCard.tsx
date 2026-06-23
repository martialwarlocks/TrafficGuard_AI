import { Badge } from '@/components/ui'
import { IndianRupee, Car, Scale } from 'lucide-react'
import type { AnalyzeResult } from '@/lib/api'

interface EnforcementCardProps {
  analysis: AnalyzeResult
}

export function EnforcementCard({ analysis }: EnforcementCardProps) {
  const summary = analysis.user_summary
  const plate = analysis.ocr_result?.text || summary?.plate_number
  const fine = analysis.fine_amount ?? summary?.fine_inr ?? 0
  const legal = analysis.legal_section || summary?.legal_section
  const violation = summary?.violation_label || analysis.violation_type?.replace(/_/g, ' ')

  return (
    <div className="grid sm:grid-cols-3 gap-3 mb-4">
      <div className="p-4 rounded-xl bg-bg border border-border">
        <div className="flex items-center gap-2 text-muted text-xs uppercase tracking-wide mb-2">
          <Car className="w-3.5 h-3.5" /> License Plate
        </div>
        {plate ? (
          <p className="font-mono text-xl font-bold tracking-wider">{plate}</p>
        ) : (
          <p className="text-sm text-warning">Not readable — officer verification required</p>
        )}
        {analysis.ocr_result?.confidence != null && plate && (
          <p className="text-xs text-muted mt-1">{(analysis.ocr_result.confidence * 100).toFixed(0)}% confidence</p>
        )}
      </div>

      <div className="p-4 rounded-xl bg-bg border border-border">
        <div className="flex items-center gap-2 text-muted text-xs uppercase tracking-wide mb-2">
          <Scale className="w-3.5 h-3.5" /> Violation
        </div>
        <p className="text-lg font-semibold capitalize">{violation || 'None detected'}</p>
        {analysis.violation_type && (
          <Badge variant="warning" className="mt-2 text-xs">MV Act offence</Badge>
        )}
      </div>

      <div className={`p-4 rounded-xl border ${fine > 0 ? 'bg-danger/10 border-danger/30' : 'bg-bg border-border'}`}>
        <div className="flex items-center gap-2 text-muted text-xs uppercase tracking-wide mb-2">
          <IndianRupee className="w-3.5 h-3.5" /> Challan Amount
        </div>
        {fine > 0 ? (
          <>
            <p className="text-2xl font-bold text-danger">₹{fine.toLocaleString('en-IN')}</p>
            {legal && <p className="text-xs text-muted mt-2 leading-relaxed">{legal}</p>}
          </>
        ) : (
          <p className="text-sm text-muted">No fine — no violation confirmed</p>
        )}
      </div>
    </div>
  )
}
