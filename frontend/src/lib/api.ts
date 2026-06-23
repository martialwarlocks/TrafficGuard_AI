const API_URL = import.meta.env.VITE_API_URL ?? ''

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
    this.token = localStorage.getItem('tg_token')
  }

  setToken(token: string | null) {
    this.token = token
    if (token) localStorage.setItem('tg_token', token)
    else localStorage.removeItem('tg_token')
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    }
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json'
    }

    const res = await fetch(`${this.baseUrl}${path}`, { ...options, headers })

    if (res.status === 401) {
      this.setToken(null)
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login?expired=1'
      }
      throw new Error('Session expired. Please log in again.')
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      const detail = err.detail
      const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : 'Request failed'
      throw new Error(message || 'Request failed')
    }
    return res.json()
  }

  login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  signup(data: { email: string; password: string; full_name: string; role?: string }) {
    return this.request('/api/v1/auth/signup', { method: 'POST', body: JSON.stringify(data) })
  }

  getMe() {
    return this.request<{ id: number; email: string; full_name: string; role: string }>('/api/v1/auth/me')
  }

  getDashboard() {
    return this.request<DashboardStats>('/api/v1/dashboard')
  }

  getViolations(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return this.request<Violation[]>(`/api/v1/violations${qs}`)
  }

  getReviewQueue() {
    return this.request<Violation[]>('/api/v1/review-queue')
  }

  submitReview(data: { violation_id: number; action: string; notes?: string }) {
    return this.request('/api/v1/review', { method: 'POST', body: JSON.stringify(data) })
  }

  getAnalytics() {
    return this.request<AnalyticsData>('/api/v1/analytics')
  }

  getHeatmap() {
    return this.request<HeatmapPoint[]>('/api/v1/heatmap')
  }

  getCameras() {
    return this.request<Camera[]>('/api/v1/cameras')
  }

  getModelMetrics() {
    return this.request<ModelMetrics>('/api/v1/model-metrics')
  }

  getHealth() {
    return this.request('/api/v1/health')
  }

  getViolationDetail(id: number) {
    return this.request<ViolationDetail>(`/api/v1/violations/${id}/detail`)
  }

  analyzeImage(file: File, cameraId?: number, liveMode = false) {
    const form = new FormData()
    form.append('file', file)
    if (cameraId) form.append('camera_id', String(cameraId))
    form.append('live_mode', liveMode ? 'true' : 'false')
    return this.request<AnalyzeResult>('/api/v1/analyze', { method: 'POST', body: form })
  }

  submitFeedback(data: { violation_id: number; is_correct: boolean; notes?: string }) {
    return this.request('/api/v1/feedback', { method: 'POST', body: JSON.stringify(data) })
  }
}

export interface DashboardStats {
  total_violations: number
  auto_processed: number
  human_reviewed: number
  review_rate: number
  avg_confidence: number
  avg_uncertainty: number
  active_cameras: number
  today_revenue: number
  system_health: number
  pending_reviews: number
}

export interface Violation {
  id: number
  violation_type: string
  camera_id?: number
  vehicle_type?: string
  plate_number?: string
  confidence: number
  uncertainty: number
  routing_decision: string
  routing_rationale?: string
  explanation?: { confidence: number; uncertainty: number; reasons: string[] }
  status: string
  latitude?: number
  longitude?: number
  fine_amount: number
  detected_at: string
}

export interface Camera {
  id: number
  name: string
  camera_id: string
  stream_url?: string
  latitude?: number
  longitude?: number
  location_name?: string
  status: string
  is_active: boolean
}

export interface AnalyticsData {
  hourly_trends: { label: string; count: number; auto: number; review: number }[]
  daily_trends: { label: string; count: number; auto: number; review: number }[]
  monthly_trends: { label: string; count: number; auto: number; review: number }[]
  violation_categories: { type: string; count: number }[]
  confidence_distribution: { bucket: number; count: number }[]
  uncertainty_distribution: { bucket: number; count: number }[]
  officer_productivity: { officer: string; reviews: number }[]
  review_accuracy: number
  model_drift: { date: string; drift: number }[]
}

export interface HeatmapPoint {
  latitude: number
  longitude: number
  intensity: number
  violation_count: number
}

export interface ModelMetrics {
  precision: number
  recall: number
  map50: number
  map50_95: number
  f1_score: number
  avg_confidence: number
  avg_uncertainty: number
  latency_ms: number
  fps: number
  gpu_utilization: number
  drift_alerts: { severity: string; message: string }[]
  retraining_status: string
}

export interface AnalyzeResult {
  violation_id?: number
  violation_type?: string
  confidence: number
  uncertainty: number
  routing_decision: string
  routing_rationale?: string
  explanation: { confidence: number; uncertainty: number; reasons: string[] }
  detections: { class_name: string; confidence: number; bbox: number[] }[]
  quality_score: number
  processing_time_ms: number
  user_summary?: UserSummary
  image_urls?: { original?: string; enhanced?: string; annotated?: string }
  ocr_result?: { text: string; confidence: number; alternatives?: { text: string; confidence: number }[] }
  traffic_signal?: { state: string; confidence: number }
  scene_context?: { crosswalk_detected: boolean; is_intersection: boolean }
  annotated_image_b64?: string
  fine_amount?: number
  legal_section?: string
}

export interface UserSummary {
  headline: string
  verdict: string
  next_step: string
  found_items: { label: string; count: number; confidence: number }[]
  plate_number?: string
  vehicle_type?: string
  inferred_violation_type?: string
  violation_label?: string
  routing_decision: string
  signal_state?: string
  fine_inr?: number
  legal_section?: string
}

export interface ViolationDetail extends Violation {
  image_urls: { original_url?: string; enhanced_url?: string; annotated_url?: string }
  ocr_result?: { text: string; confidence: number }
  detection_data?: { class_name: string; confidence: number; bbox: number[] }[]
}

export const api = new ApiClient(API_URL)
