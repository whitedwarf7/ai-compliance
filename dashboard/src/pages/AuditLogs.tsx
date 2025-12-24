import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Search, FileText } from 'lucide-react'
import { api } from '../api/client'
import { format } from 'date-fns'
import type { AuditLog } from '../types'

const demoLogs: AuditLog[] = Array.from({ length: 20 }, (_, i) => ({
  id: `log-${i}`,
  org_id: 'demo-org',
  app_id: ['customer-support', 'sales-assistant', 'hr-chatbot', 'code-assistant'][i % 4],
  user_id: `user-${i % 5}`,
  model: ['gpt-4o', 'gpt-3.5-turbo', 'gpt-4-turbo'][i % 3],
  provider: 'openai',
  prompt_hash: `hash-${i}`,
  token_count_input: Math.floor(Math.random() * 500) + 50,
  token_count_output: Math.floor(Math.random() * 300) + 20,
  latency_ms: Math.floor(Math.random() * 2000) + 200,
  risk_flags: i % 3 === 0 ? ['EMAIL'] : [],
  metadata: {},
  created_at: new Date(Date.now() - i * 1800000).toISOString(),
}))

export default function AuditLogs() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    model: '',
    app_id: '',
  })
  
  const { data, isLoading } = useQuery({
    queryKey: ['logs', page, filters],
    queryFn: () => api.getLogs({ page, limit: 20, ...filters }),
    placeholderData: { items: demoLogs, total: 100, page: 1, limit: 20, pages: 5 },
  })
  
  const logs = data?.items || demoLogs
  const totalPages = data?.pages || 5
  
  const handleExport = async () => {
    try {
      const blob = await api.exportLogsCSV(filters)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audit_logs_${format(new Date(), 'yyyyMMdd')}.csv`
      a.click()
    } catch (error) {
      console.error('Export failed:', error)
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Search and filters */}
      <div className="card">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center flex-1 gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by app, user, or model..."
                className="input pl-10 w-full"
              />
            </div>
            
            <select
              value={filters.model}
              onChange={(e) => setFilters({ ...filters, model: e.target.value })}
              className="input"
            >
              <option value="">All Models</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
          
          <button onClick={handleExport} className="btn-secondary flex items-center">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>
      
      {/* Logs table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Timestamp</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Application</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Model</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Tokens</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Latency</th>
              <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Risk Flags</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                  Loading...
                </td>
              </tr>
            ) : (
              logs.map((log: AuditLog) => (
                <tr key={log.id} className="hover:bg-slate-700/50 transition-colors">
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {format(new Date(log.created_at), 'MMM d, HH:mm:ss')}
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-medium text-white">{log.app_id}</span>
                    {log.user_id && (
                      <span className="block text-xs text-slate-400">{log.user_id}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">{log.model}</td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    <span className="text-success-500">{log.token_count_input}</span>
                    {' / '}
                    <span className="text-primary-400">{log.token_count_output}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {log.latency_ms}ms
                  </td>
                  <td className="px-6 py-4">
                    {log.risk_flags.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {log.risk_flags.map((flag: string) => (
                          <span key={flag} className="badge badge-danger">{flag}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          Showing page {page} of {totalPages}
        </p>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="btn-secondary disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
      
      {/* Empty state */}
      {!isLoading && logs.length === 0 && (
        <div className="card text-center py-12">
          <FileText className="h-12 w-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No logs found</h3>
          <p className="text-slate-400">
            Audit logs will appear here once AI requests are made through the gateway.
          </p>
        </div>
      )}
    </div>
  )
}


