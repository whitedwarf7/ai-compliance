import { ArrowUp, ArrowDown, LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  trend?: 'up' | 'down'
  icon?: LucideIcon
  iconColor?: string
}

export default function MetricCard({
  title,
  value,
  change,
  trend,
  icon: Icon,
  iconColor = 'text-primary-500',
}: MetricCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-white">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {change !== undefined && (
            <div className="mt-2 flex items-center">
              {trend === 'up' ? (
                <ArrowUp className="h-4 w-4 text-success-500" />
              ) : trend === 'down' ? (
                <ArrowDown className="h-4 w-4 text-danger-500" />
              ) : null}
              <span
                className={clsx(
                  'ml-1 text-sm',
                  trend === 'up' ? 'text-success-500' : 'text-danger-500'
                )}
              >
                {Math.abs(change)}%
              </span>
              <span className="ml-1 text-sm text-slate-400">vs last period</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={clsx('p-3 rounded-lg bg-slate-700/50', iconColor)}>
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
    </div>
  )
}


