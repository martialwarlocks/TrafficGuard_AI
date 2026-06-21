import { useState } from 'react'
import { Card, Badge, Button, Input } from '@/components/ui'
import { Settings, Users, Camera, Sliders, Bell, Cpu } from 'lucide-react'

const tabs = [
  { id: 'users', label: 'Users', icon: Users },
  { id: 'cameras', label: 'Cameras', icon: Camera },
  { id: 'thresholds', label: 'Thresholds', icon: Sliders },
  { id: 'alerts', label: 'Alert Rules', icon: Bell },
  { id: 'model', label: 'Model Settings', icon: Cpu },
  { id: 'system', label: 'System', icon: Settings },
]

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('thresholds')
  const [thresholds, setThresholds] = useState({ auto: 0.85, review: 0.60, quality: 0.40 })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted text-sm">Manage users, cameras, thresholds, and system configuration</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
              activeTab === id ? 'bg-primary text-white' : 'bg-card text-muted hover:text-text'
            }`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {activeTab === 'thresholds' && (
        <Card>
          <h3 className="font-semibold mb-6">Routing Thresholds</h3>
          <div className="space-y-6 max-w-md">
            <div>
              <label className="text-sm text-muted block mb-2">Auto Process Threshold: {(thresholds.auto * 100).toFixed(0)}%</label>
              <input type="range" min="0.7" max="0.95" step="0.01" value={thresholds.auto}
                onChange={(e) => setThresholds({ ...thresholds, auto: parseFloat(e.target.value) })}
                className="w-full accent-primary" />
              <p className="text-xs text-muted mt-1">Confidence ≥ this value → Auto Process</p>
            </div>
            <div>
              <label className="text-sm text-muted block mb-2">Human Review Threshold: {(thresholds.review * 100).toFixed(0)}%</label>
              <input type="range" min="0.4" max="0.84" step="0.01" value={thresholds.review}
                onChange={(e) => setThresholds({ ...thresholds, review: parseFloat(e.target.value) })}
                className="w-full accent-warning" />
              <p className="text-xs text-muted mt-1">Confidence between review and auto → Human Review</p>
            </div>
            <div>
              <label className="text-sm text-muted block mb-2">Minimum Quality Score: {(thresholds.quality * 100).toFixed(0)}%</label>
              <input type="range" min="0.2" max="0.8" step="0.01" value={thresholds.quality}
                onChange={(e) => setThresholds({ ...thresholds, quality: parseFloat(e.target.value) })}
                className="w-full accent-success" />
            </div>
            <Button>Save Thresholds</Button>
          </div>
        </Card>
      )}

      {activeTab === 'users' && (
        <Card>
          <h3 className="font-semibold mb-4">User Management</h3>
          <div className="space-y-3">
            {[
              { name: 'System Administrator', email: 'admin@trafficguard.ai', role: 'Admin' },
              { name: 'Demo Officer', email: 'officer@trafficguard.ai', role: 'Officer' },
              { name: 'Demo Supervisor', email: 'supervisor@trafficguard.ai', role: 'Supervisor' },
            ].map((u) => (
              <div key={u.email} className="flex items-center justify-between p-3 rounded-lg bg-bg">
                <div>
                  <p className="font-medium text-sm">{u.name}</p>
                  <p className="text-xs text-muted">{u.email}</p>
                </div>
                <Badge>{u.role}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'cameras' && (
        <Card>
          <h3 className="font-semibold mb-4">Camera Management</h3>
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <Input placeholder="Camera Name" />
            <Input placeholder="RTSP Stream URL" />
          </div>
          <Button>Add Camera</Button>
        </Card>
      )}

      {activeTab === 'model' && (
        <Card>
          <h3 className="font-semibold mb-4">Model Settings</h3>
          <div className="space-y-4 text-sm">
            <div className="flex justify-between p-3 rounded-lg bg-bg">
              <span className="text-muted">YOLO Model</span><span>yolov8s.pt</span>
            </div>
            <div className="flex justify-between p-3 rounded-lg bg-bg">
              <span className="text-muted">MC Dropout Passes</span><span>20</span>
            </div>
            <div className="flex justify-between p-3 rounded-lg bg-bg">
              <span className="text-muted">OCR Engine</span><span>PaddleOCR</span>
            </div>
            <div className="flex justify-between p-3 rounded-lg bg-bg">
              <span className="text-muted">Enhancement</span><span>CLAHE + Denoise + Sharpen</span>
            </div>
          </div>
        </Card>
      )}

      {(activeTab === 'alerts' || activeTab === 'system') && (
        <Card>
          <h3 className="font-semibold mb-4 capitalize">{activeTab.replace('-', ' ')} Configuration</h3>
          <p className="text-muted text-sm">Configure {activeTab} settings through the admin API.</p>
        </Card>
      )}
    </div>
  )
}
