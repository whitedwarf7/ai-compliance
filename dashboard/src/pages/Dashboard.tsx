import { useQuery } from '@tanstack/react-query'
import { Activity, AlertTriangle, ShieldCheck, Zap } from 'lucide-react'
import MetricCard from '../components/MetricCard'
import ViolationChart from '../components/charts/ViolationChart'
import PieChartComponent from '../components/charts/PieChartComponent'
import { api } from '../api/client'
import type { ViolationSummary, LogStats } from '../types'

// Demo data for when API is not available
const demoStats: LogStats = {
  total_requests: 15847,
  total_tokens_input: 2456000,
  total_tokens_output: 892000,
  unique_models: 5,
  unique_apps: 12,
  requests_with_risk_flags: 342,
}

const demoSummary: ViolationSummary = {
  total_violations: 342,
  total_blocked: 89,
  total_masked: 178,
  total_warned: 75,
  by_type: { EMAIL: 145, PHONE: 87, CREDIT_CARD: 45, PAN: 32, AADHAAR: 23, SSN: 10 },
  by_action: { blocked: 89, masked: 178, warned: 75 },
  by_severity: { critical: 110, high: 87, medium: 145 },
  top_violating_apps: [
    { app_id: 'customer-support', violation_count: 89 },
    { app_id: 'sales-assistant', violation_count: 67 },
    { app_id: 'hr-chatbot', violation_count: 54 },
  ],
  top_violating_orgs: [],
  recent_violations: [],
}

const demoTrends = {
  trends: Array.from({ length: 30 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (29 - i))
    return {
      date: date.toISOString().split('T')[0],
      total: Math.floor(Math.random() * 20) + 5,
      blocked: Math.floor(Math.random() * 8) + 1,
      masked: Math.floor(Math.random() * 10) + 2,
      warned: Math.floor(Math.random() * 5) + 1,
    }
  }),
}

export default function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getLogStats(),
    placeholderData: demoStats,
  })
  
  const { data: summary } = useQuery({
    queryKey: ['violations-summary'],
    queryFn: () => api.getViolationsSummary(),
    placeholderData: demoSummary,
  })
  
  const { data: trends } = useQuery({
    queryKey: ['violations-trends'],
    queryFn: () => api.getViolationsTrends(30),
    placeholderData: demoTrends,
  })
  
  const piiTypeData = Object.entries(summary?.by_type || {}).map(([name, value]) => ({
    name,
    value: value as number,
  }))
  
  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total AI Requests"
          value={stats?.total_requests || 0}
          change={12}
          trend="up"
          icon={Activity}
          iconColor="text-primary-500"
        />
        <MetricCard
          title="Policy Violations"
          value={summary?.total_violations || 0}
          change={-8}
          trend="down"
          icon={AlertTriangle}
          iconColor="text-danger-500"
        />
        <MetricCard
          title="Requests Blocked"
          value={summary?.total_blocked || 0}
          icon={ShieldCheck}
          iconColor="text-success-500"
        />
        <MetricCard
          title="Tokens Processed"
          value={`${((stats?.total_tokens_input || 0) / 1000000).toFixed(1)}M`}
          change={15}
          trend="up"
          icon={Zap}
          iconColor="text-warning-500"
        />
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-medium text-white mb-4">Violation Trends (30 days)</h3>
          <ViolationChart data={trends?.trends || []} />
        </div>
        
        <div className="card">
          <h3 className="text-lg font-medium text-white mb-4">Violations by PII Type</h3>
          <PieChartComponent data={piiTypeData} />
        </div>
      </div>
      
      {/* Recent violations and top apps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-white mb-4">Top Violating Applications</h3>
          <div className="space-y-3">
            {(summary?.top_violating_apps || []).slice(0, 5).map((app: { app_id: string; violation_count: number }, index: number) => (
              <div key={app.app_id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div className="flex items-center">
                  <span className="w-6 h-6 flex items-center justify-center rounded-full bg-slate-600 text-xs text-white mr-3">
                    {index + 1}
                  </span>
                  <span className="text-white font-medium">{app.app_id}</span>
                </div>
                <span className="badge badge-danger">{app.violation_count} violations</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-medium text-white mb-4">Action Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-danger-500/10 rounded-lg border border-danger-500/30">
              <p className="text-2xl font-bold text-danger-500">{summary?.total_blocked || 0}</p>
              <p className="text-sm text-slate-400 mt-1">Blocked</p>
            </div>
            <div className="text-center p-4 bg-warning-500/10 rounded-lg border border-warning-500/30">
              <p className="text-2xl font-bold text-warning-500">{summary?.total_masked || 0}</p>
              <p className="text-sm text-slate-400 mt-1">Masked</p>
            </div>
            <div className="text-center p-4 bg-primary-500/10 rounded-lg border border-primary-500/30">
              <p className="text-2xl font-bold text-primary-400">{summary?.total_warned || 0}</p>
              <p className="text-sm text-slate-400 mt-1">Warned</p>
            </div>
          </div>
          
          <div className="mt-6">
            <h4 className="text-sm font-medium text-slate-300 mb-3">Severity Breakdown</h4>
            <div className="space-y-2">
              {Object.entries(summary?.by_severity || {}).map(([severity, count]) => (
                <div key={severity} className="flex items-center">
                  <span className="w-20 text-sm text-slate-400 capitalize">{severity}</span>
                  <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        severity === 'critical' ? 'bg-danger-500' :
                        severity === 'high' ? 'bg-warning-500' :
                        'bg-primary-500'
                      }`}
                      style={{ width: `${((count as number) / (summary?.total_violations || 1)) * 100}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-sm text-slate-400">{count as number}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


