import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  AlertTriangle,
  FileText,
  Shield,
  Settings,
  LogOut,
} from 'lucide-react'
import { useAuthStore } from '../store/auth'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Violations', href: '/violations', icon: AlertTriangle },
  { name: 'Audit Logs', href: '/logs', icon: FileText },
  { name: 'Policies', href: '/policies', icon: Shield },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  
  return (
    <div className="fixed inset-y-0 left-0 w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-700">
        <Shield className="h-8 w-8 text-primary-500" />
        <span className="ml-3 text-lg font-semibold text-white">
          AI Compliance
        </span>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              clsx(
                'flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              )
            }
          >
            <item.icon className="h-5 w-5 mr-3" />
            {item.name}
          </NavLink>
        ))}
      </nav>
      
      {/* User section */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center">
          <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-medium">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div className="ml-3 flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user?.name || 'User'}
            </p>
            <p className="text-xs text-slate-400 truncate">
              {user?.role || 'viewer'}
            </p>
          </div>
          <button
            onClick={logout}
            className="p-2 text-slate-400 hover:text-white transition-colors"
            title="Logout"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}


