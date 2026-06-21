import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, Eye, Layers, Zap, Brain, Users, BarChart } from 'lucide-react'
import { Button } from '@/components/ui'

const features = [
  { icon: Brain, title: 'Uncertainty-Aware Routing', desc: 'High confidence auto-processes. Borderline cases go to human review. Low confidence is discarded.' },
  { icon: Eye, title: 'Explainable AI', desc: 'Every decision includes natural-language reasoning: occlusion, blur, OCR disagreement, and more.' },
  { icon: Users, title: 'Officer Feedback Loop', desc: 'Continuous learning through officer approvals, rejections, and corrections.' },
  { icon: Zap, title: 'Real-Time Detection', desc: 'YOLOv8s + PaddleOCR pipeline with MC Dropout uncertainty estimation.' },
  { icon: Layers, title: 'Evidence Chain of Custody', desc: 'SHA256 hashing, tamper detection, and forensic-grade evidence portal.' },
  { icon: BarChart, title: 'Smart City Analytics', desc: 'Heatmaps, digital twin, model drift monitoring, and safety scoring.' },
]

const stats = [
  { label: 'Detection Accuracy', value: '89%' },
  { label: 'Avg Processing Time', value: '45ms' },
  { label: 'Review Rate Reduction', value: '62%' },
  { label: 'False Positive Reduction', value: '78%' },
]

export function LandingPage() {
  return (
    <div className="min-h-screen bg-bg text-text overflow-hidden">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(79,140,255,0.08)_0%,_transparent_60%)]" />
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-primary/30 rounded-full"
            initial={{ x: Math.random() * (typeof window !== 'undefined' ? window.innerWidth : 1200), y: -10 }}
            animate={{ y: (typeof window !== 'undefined' ? window.innerHeight : 800) + 10 }}
            transition={{ duration: 8 + Math.random() * 12, repeat: Infinity, delay: Math.random() * 5 }}
          />
        ))}
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <Shield className="w-8 h-8 text-primary" />
          <span className="font-bold text-lg">TrafficGuard AI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login"><Button variant="ghost">Sign In</Button></Link>
          <Link to="/dashboard"><Button>Launch Dashboard</Button></Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 max-w-7xl mx-auto px-8 pt-20 pb-32 text-center">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-sm text-primary mb-8">
            <Zap className="w-4 h-4" /> Next-Generation Traffic Enforcement
          </div>
          <h1 className="text-5xl md:text-7xl font-bold mb-4">
            TrafficGuard <span className="gradient-text">AI</span>
          </h1>
          <p className="text-2xl md:text-3xl font-light text-muted mb-2">
            Confident Enforcement.
          </p>
          <p className="text-2xl md:text-3xl font-light text-primary mb-8">
            Humble Flagging.
          </p>
          <p className="text-lg text-muted max-w-2xl mx-auto mb-12">
            An uncertainty-aware traffic violation detection platform designed for smart cities and modern law enforcement.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/dashboard"><Button size="lg">Launch Dashboard <ArrowRight className="w-4 h-4 ml-2" /></Button></Link>
            <Link to="/login"><Button variant="secondary" size="lg">View Architecture</Button></Link>
            <Link to="/monitoring"><Button variant="ghost" size="lg">Watch Demo</Button></Link>
          </div>
        </motion.div>

        {/* Live stats */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20 max-w-3xl mx-auto"
        >
          {stats.map((s) => (
            <div key={s.label} className="glass rounded-xl p-4">
              <p className="text-2xl font-bold text-primary">{s.value}</p>
              <p className="text-xs text-muted mt-1">{s.label}</p>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section className="relative z-10 max-w-7xl mx-auto px-8 py-20">
        <h2 className="text-3xl font-bold text-center mb-4">Core Innovation</h2>
        <p className="text-muted text-center mb-12 max-w-xl mx-auto">
          Three novel capabilities that set TrafficGuard AI apart from traditional enforcement systems.
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="glass rounded-xl p-6 hover:border-primary/30 transition-colors"
            >
              <f.icon className="w-8 h-8 text-primary mb-4" />
              <h3 className="font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-muted">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Architecture overview */}
      <section className="relative z-10 max-w-7xl mx-auto px-8 py-20">
        <div className="glass rounded-2xl p-8 md:p-12">
          <h2 className="text-3xl font-bold mb-8 text-center">System Architecture</h2>
          <div className="grid md:grid-cols-5 gap-4 text-center text-sm">
            {['Capture', 'Quality Check', 'YOLO Detect', 'OCR + Uncertainty', 'Route Decision'].map((step, i) => (
              <div key={step} className="relative">
                <div className="w-12 h-12 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center mx-auto mb-2 text-primary font-bold">
                  {i + 1}
                </div>
                <p className="font-medium">{step}</p>
                {i < 4 && <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-px bg-primary/30" />}
              </div>
            ))}
          </div>
          <div className="flex justify-center gap-4 mt-8 flex-wrap">
            <span className="px-3 py-1 rounded-full bg-success/20 text-success text-xs">≥85% Auto Process</span>
            <span className="px-3 py-1 rounded-full bg-warning/20 text-warning text-xs">60-84% Human Review</span>
            <span className="px-3 py-1 rounded-full bg-danger/20 text-danger text-xs">&lt;60% Discard</span>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="relative z-10 text-center py-20">
        <h2 className="text-3xl font-bold mb-4">Ready to transform traffic enforcement?</h2>
        <Link to="/dashboard"><Button size="lg">Get Started <ArrowRight className="w-4 h-4 ml-2" /></Button></Link>
      </section>
    </div>
  )
}
