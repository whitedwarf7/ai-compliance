import { useState } from 'react'
import { useAuthStore } from '../store/auth'
import { User, Bell, Shield, Key, Save } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Settings() {
  const { user } = useAuthStore()
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    slackAlerts: true,
    dailyDigest: false,
  })
  
  const handleSave = () => {
    toast.success('Settings saved successfully')
  }
  
  return (
    <div className="max-w-4xl space-y-6">
      {/* Profile */}
      <div className="card">
        <div className="flex items-center mb-6">
          <User className="h-5 w-5 text-primary-500 mr-2" />
          <h2 className="text-lg font-medium text-white">Profile</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Name</label>
            <input
              type="text"
              defaultValue={user?.name}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
            <input
              type="email"
              defaultValue={user?.email}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Role</label>
            <input
              type="text"
              value={user?.role || 'viewer'}
              disabled
              className="input w-full bg-slate-700/50 cursor-not-allowed"
            />
          </div>
        </div>
      </div>
      
      {/* Notifications */}
      <div className="card">
        <div className="flex items-center mb-6">
          <Bell className="h-5 w-5 text-primary-500 mr-2" />
          <h2 className="text-lg font-medium text-white">Notifications</h2>
        </div>
        
        <div className="space-y-4">
          <label className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg cursor-pointer">
            <div>
              <p className="text-white font-medium">Email Alerts</p>
              <p className="text-sm text-slate-400">Receive violation alerts via email</p>
            </div>
            <input
              type="checkbox"
              checked={notifications.emailAlerts}
              onChange={(e) => setNotifications({ ...notifications, emailAlerts: e.target.checked })}
              className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-primary-500 focus:ring-primary-500"
            />
          </label>
          
          <label className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg cursor-pointer">
            <div>
              <p className="text-white font-medium">Slack Alerts</p>
              <p className="text-sm text-slate-400">Send violations to Slack channel</p>
            </div>
            <input
              type="checkbox"
              checked={notifications.slackAlerts}
              onChange={(e) => setNotifications({ ...notifications, slackAlerts: e.target.checked })}
              className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-primary-500 focus:ring-primary-500"
            />
          </label>
          
          <label className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg cursor-pointer">
            <div>
              <p className="text-white font-medium">Daily Digest</p>
              <p className="text-sm text-slate-400">Receive daily summary of activity</p>
            </div>
            <input
              type="checkbox"
              checked={notifications.dailyDigest}
              onChange={(e) => setNotifications({ ...notifications, dailyDigest: e.target.checked })}
              className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-primary-500 focus:ring-primary-500"
            />
          </label>
        </div>
      </div>
      
      {/* Security */}
      <div className="card">
        <div className="flex items-center mb-6">
          <Shield className="h-5 w-5 text-primary-500 mr-2" />
          <h2 className="text-lg font-medium text-white">Security</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Current Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className="input w-full max-w-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">New Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className="input w-full max-w-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Confirm New Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className="input w-full max-w-md"
            />
          </div>
        </div>
      </div>
      
      {/* API Keys */}
      <div className="card">
        <div className="flex items-center mb-6">
          <Key className="h-5 w-5 text-primary-500 mr-2" />
          <h2 className="text-lg font-medium text-white">API Keys</h2>
        </div>
        
        <p className="text-slate-400 mb-4">
          API keys are used to authenticate applications with the AI Compliance Gateway.
        </p>
        
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-mono text-sm">sk-compliance-****-****-****-demo</p>
              <p className="text-xs text-slate-400 mt-1">Created: Jan 15, 2024</p>
            </div>
            <button className="btn-danger text-sm">Revoke</button>
          </div>
        </div>
        
        <button className="btn-secondary mt-4">
          Generate New Key
        </button>
      </div>
      
      {/* Save button */}
      <div className="flex justify-end">
        <button onClick={handleSave} className="btn-primary flex items-center">
          <Save className="h-4 w-4 mr-2" />
          Save Changes
        </button>
      </div>
    </div>
  )
}


