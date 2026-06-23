import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield } from 'lucide-react'
import { Button, Input, Card } from '@/components/ui'
import { useAuthStore } from '@/store'

export function LoginPage() {
  const [email, setEmail] = useState('admin@trafficguard.ai')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const { login, isLoading } = useAuthStore()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionExpired = searchParams.get('expired') === '1'

  useEffect(() => {
    if (sessionExpired) {
      useAuthStore.getState().logout()
    }
  }, [sessionExpired])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="w-full max-w-md glass">
          <div className="text-center mb-8">
            <Shield className="w-12 h-12 text-primary mx-auto mb-4" />
            <h1 className="text-2xl font-bold">Sign In</h1>
            <p className="text-muted text-sm mt-1">TrafficGuard AI Command Center</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-muted mb-1 block">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="text-sm text-muted mb-1 block">Password</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {sessionExpired && (
              <p className="text-warning text-sm bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
                Your session expired. Please sign in again.
              </p>
            )}
            {error && <p className="text-danger text-sm">{error}</p>}
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-muted space-y-2">
            <Link to="/forgot-password" className="text-primary hover:underline block">Forgot password?</Link>
            <Link to="/signup" className="hover:text-text block">Create an account</Link>
            <Link to="/" className="hover:text-text block">← Back to home</Link>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}

export function SignupPage() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'officer' })
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { api } = await import('@/lib/api')
      await api.signup(form)
      navigate('/login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed')
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <Card className="w-full max-w-md glass">
        <h1 className="text-2xl font-bold text-center mb-6">Create Account</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input placeholder="Full Name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          <Input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <Input type="password" placeholder="Password (min 8 chars)" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <select
            className="w-full h-10 px-3 rounded-lg bg-bg border border-border text-text"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="officer">Officer</option>
            <option value="supervisor">Supervisor</option>
            <option value="analyst">Analyst</option>
          </select>
          {error && <p className="text-danger text-sm">{error}</p>}
          <Button type="submit" className="w-full">Sign Up</Button>
        </form>
        <p className="text-center text-sm text-muted mt-4">
          <Link to="/login" className="text-primary hover:underline">Already have an account?</Link>
        </p>
      </Card>
    </div>
  )
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSent(true)
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <Card className="w-full max-w-md glass">
        <h1 className="text-2xl font-bold text-center mb-6">Reset Password</h1>
        {sent ? (
          <p className="text-center text-muted">If the email exists, a reset link has been sent.</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input type="email" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Button type="submit" className="w-full">Send Reset Link</Button>
          </form>
        )}
        <p className="text-center text-sm text-muted mt-4">
          <Link to="/login" className="text-primary hover:underline">Back to login</Link>
        </p>
      </Card>
    </div>
  )
}
