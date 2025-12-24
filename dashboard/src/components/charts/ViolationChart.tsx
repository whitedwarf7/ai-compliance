import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { ViolationTrend } from '../../types'

interface ViolationChartProps {
  data: ViolationTrend[]
}

export default function ViolationChart({ data }: ViolationChartProps) {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorMasked" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorWarned" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            stroke="#94a3b8"
            fontSize={12}
            tickFormatter={(value) => {
              const date = new Date(value)
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            }}
          />
          <YAxis stroke="#94a3b8" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f1f5f9' }}
          />
          <Area
            type="monotone"
            dataKey="blocked"
            stackId="1"
            stroke="#ef4444"
            fill="url(#colorBlocked)"
            name="Blocked"
          />
          <Area
            type="monotone"
            dataKey="masked"
            stackId="1"
            stroke="#f59e0b"
            fill="url(#colorMasked)"
            name="Masked"
          />
          <Area
            type="monotone"
            dataKey="warned"
            stackId="1"
            stroke="#0ea5e9"
            fill="url(#colorWarned)"
            name="Warned"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}


