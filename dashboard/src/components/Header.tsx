import { useLocation } from 'react-router-dom'
import { Bell, Search } from 'lucide-react'

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/violations': 'Violations',
  '/logs': 'Audit Logs',
  '/policies': 'Policies',
  '/settings': 'Settings',
}

export default function Header() {
  const location = useLocation()
  const title = pageTitles[location.pathname] || 'Dashboard'
  
  return (
    <header className="h-16 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-6">
      <h1 className="text-xl font-semibold text-white">{title}</h1>
      
      <div className="flex items-center space-x-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search..."
            className="input pl-10 w-64"
          />
        </div>
        
        {/* Notifications */}
        <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full"></span>
        </button>
      </div>
    </header>
  )
}


