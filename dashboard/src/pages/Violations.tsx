import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Filter, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'
import { format } from 'date-fns'
import clsx from 'clsx'
import type { Violation } from '../types'

const demoViolations: Violation[] = Array.from({ length: 20 }, (_, i) => ({
  id: `viol-${i}`,
  org_id: 'demo-org',
  app_id: ['customer-support', 'sales-assistant', 'hr-chatbot'][i % 3],
  user_id: `user-${i % 5}`,
  model: ['gpt-4o', 'gpt-3.5-turbo', 'gpt-4-turbo'][i % 3],
  risk_flags: [['EMAIL'], ['PHONE', 'EMAIL'], ['CREDIT_CARD'], ['PAN'], ['AADHAAR']][i % 5],
  action: ['blocked', 'masked', 'warned'][i % 3] as Violation['action'],
  created_at: new Date(Date.now() - i * 3600000).toISOString(),
}))

export default function Violations() {
  const [filters, setFilters] = useState({
    pii_type: '',
    action: '',
    page: 1,
  })
  
  const { data: violations, isLoading } = useQuery({
    queryKey: ['violations', filters],
    queryFn: () => api.getViolations(filters),
    placeholderData: demoViolations,
  })
  
  const handleExport = async () => {
    try {
      const blob = await api.exportLogsCSV({ has_risk_flags: true })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `violations_${format(new Date(), 'yyyyMMdd')}.csv`
      a.click()
    } catch (error) {
      console.error('Export failed:', error)
    }
  }
  
  const getActionBadge = (action: string) => {
    switch (action) {
      case 'blocked':
        return <span className="badge badge-danger">Blocked</span>
      case 'masked':
        return <span className="badge badge-warning">Masked</span>
      case 'warned':
        return <span className="badge badge-info">Warned</span>
      default:
        return <span className="badge">{action}</span>
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-slate-400" />
              <span className="text-slate-300">Filters:</span>
            </div>
            
            <select
              value={filters.pii_type}
              onChange={(e) => setFilters({ ...filters, pii_type: e.target.value })}
              className="input"
            >
              <option value="">All PII Types</option>
              <option value="EMAIL">Email</option>
              <option value="PHONE">Phone</option>
              <option value="CREDIT_CARD">Credit Card</option>
              <option value="PAN">PAN</option>
              <option value="AADHAAR">Aadhaar</option>
              <option value="SSN">SSN</option>
            </select>
            
            <select
              value={filters.action}
              onChange={(e) => setFilters({ ...filters, action: e.target.value })}
              className="input"
            >
              <option value="">All Actions</option>
              <option value="blocked">Blocked</option>
              <option value="masked">Masked</option>
              <option value="warned">Warned</option>
            </select>
          </div>
          
          <button onClick={handleExport} className="btn-secondary flex items-center">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>
      
      {/* Violations table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Timestamp</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Application</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Model</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">PII Types</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                  Loading...
                </td>
              </tr>
            ) : (
              (Array.isArray(violations) ? violations : demoViolations).map((violation) => (
                <tr key={violation.id} className="hover:bg-slate-700/50 transition-colors">
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {format(new Date(violation.created_at), 'MMM d, yyyy HH:mm')}
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-medium text-white">{violation.app_id}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">{violation.model}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {violation.risk_flags.map((flag: string) => (
                        <span
                          key={flag}
                          className={clsx(
                            'badge',
                            ['AADHAAR', 'PAN', 'CREDIT_CARD', 'SSN'].includes(flag)
                              ? 'badge-danger'
                              : 'badge-warning'
                          )}
                        >
                          {flag}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4">{getActionBadge(violation.action)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Empty state */}
      {!isLoading && (!violations || violations.length === 0) && (
        <div className="card text-center py-12">
          <AlertTriangle className="h-12 w-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No violations found</h3>
          <p className="text-slate-400">
            Great news! There are no policy violations matching your filters.
          </p>
        </div>
      )}
    </div>
  )
}


