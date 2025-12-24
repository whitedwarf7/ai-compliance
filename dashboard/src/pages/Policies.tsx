import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Shield, AlertCircle, CheckCircle } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const demoPolicy = {
  name: 'Default Compliance Policy',
  version: '1.0',
  description: 'Default policy that blocks critical PII and masks medium PII',
  rules: {
    block_if: ['AADHAAR', 'PAN', 'CREDIT_CARD', 'SSN'],
    mask_if: ['EMAIL', 'PHONE'],
    warn_if: ['IP_ADDRESS', 'DATE_OF_BIRTH'],
    allowed_models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
    blocked_models: [],
    allowed_apps: ['*'],
    blocked_apps: [],
  },
  org_overrides: [],
}

export default function Policies() {
  const queryClient = useQueryClient()
  
  const { data: policy } = useQuery({
    queryKey: ['policy'],
    queryFn: () => api.getPolicy(),
    placeholderData: demoPolicy,
  })
  
  const reloadMutation = useMutation({
    mutationFn: () => api.reloadPolicy(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policy'] })
      toast.success('Policy reloaded successfully')
    },
    onError: () => {
      toast.error('Failed to reload policy')
    },
  })
  
  const currentPolicy = policy || demoPolicy
  
  return (
    <div className="space-y-6">
      {/* Policy header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-primary-500 mr-4" />
            <div>
              <h2 className="text-xl font-semibold text-white">{currentPolicy.name}</h2>
              <p className="text-sm text-slate-400">Version {currentPolicy.version}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => reloadMutation.mutate()}
              disabled={reloadMutation.isPending}
              className="btn-secondary flex items-center"
            >
              <RefreshCw className={clsx('h-4 w-4 mr-2', reloadMutation.isPending && 'animate-spin')} />
              Reload Policy
            </button>
          </div>
        </div>
        
        {currentPolicy.description && (
          <p className="mt-4 text-slate-300">{currentPolicy.description}</p>
        )}
      </div>
      
      {/* Policy rules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Block rules */}
        <div className="card">
          <div className="flex items-center mb-4">
            <AlertCircle className="h-5 w-5 text-danger-500 mr-2" />
            <h3 className="text-lg font-medium text-white">Block If Detected</h3>
          </div>
          <p className="text-sm text-slate-400 mb-4">
            Requests containing these PII types will be blocked immediately.
          </p>
          <div className="flex flex-wrap gap-2">
            {currentPolicy.rules.block_if.map((type: string) => (
              <span key={type} className="badge badge-danger text-sm px-3 py-1">
                {type}
              </span>
            ))}
          </div>
        </div>
        
        {/* Mask rules */}
        <div className="card">
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-warning-500 mr-2" />
            <h3 className="text-lg font-medium text-white">Mask Before Forwarding</h3>
          </div>
          <p className="text-sm text-slate-400 mb-4">
            These PII types will be replaced with [TYPE_REDACTED] before sending to AI.
          </p>
          <div className="flex flex-wrap gap-2">
            {currentPolicy.rules.mask_if.map((type: string) => (
              <span key={type} className="badge badge-warning text-sm px-3 py-1">
                {type}
              </span>
            ))}
          </div>
        </div>
        
        {/* Warn rules */}
        <div className="card">
          <div className="flex items-center mb-4">
            <AlertCircle className="h-5 w-5 text-primary-400 mr-2" />
            <h3 className="text-lg font-medium text-white">Warn Only</h3>
          </div>
          <p className="text-sm text-slate-400 mb-4">
            Log a warning but allow the request to proceed.
          </p>
          <div className="flex flex-wrap gap-2">
            {currentPolicy.rules.warn_if.length > 0 ? (
              currentPolicy.rules.warn_if.map((type: string) => (
                <span key={type} className="badge badge-info text-sm px-3 py-1">
                  {type}
                </span>
              ))
            ) : (
              <span className="text-slate-500">None configured</span>
            )}
          </div>
        </div>
        
        {/* Allowed models */}
        <div className="card">
          <div className="flex items-center mb-4">
            <CheckCircle className="h-5 w-5 text-success-500 mr-2" />
            <h3 className="text-lg font-medium text-white">Allowed Models</h3>
          </div>
          <p className="text-sm text-slate-400 mb-4">
            Only these AI models can be used through the gateway.
          </p>
          <div className="flex flex-wrap gap-2">
            {currentPolicy.rules.allowed_models.length > 0 ? (
              currentPolicy.rules.allowed_models.map((model: string) => (
                <span key={model} className="badge badge-success text-sm px-3 py-1">
                  {model}
                </span>
              ))
            ) : (
              <span className="text-slate-400">All models allowed</span>
            )}
          </div>
        </div>
      </div>
      
      {/* Policy YAML preview */}
      <div className="card">
        <h3 className="text-lg font-medium text-white mb-4">Policy Configuration (YAML)</h3>
        <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto text-sm font-mono text-slate-300">
{`version: "${currentPolicy.version}"
name: "${currentPolicy.name}"

rules:
  block_if:
${currentPolicy.rules.block_if.map((t: string) => `    - ${t}`).join('\n')}
  
  mask_if:
${currentPolicy.rules.mask_if.map((t: string) => `    - ${t}`).join('\n')}
  
  warn_if:
${currentPolicy.rules.warn_if.map((t: string) => `    - ${t}`).join('\n')}
  
  allowed_models:
${currentPolicy.rules.allowed_models.map((m: string) => `    - ${m}`).join('\n')}`}
        </pre>
        <p className="mt-4 text-sm text-slate-400">
          To modify the policy, edit the <code className="text-primary-400">policies/default.yaml</code> file
          and click "Reload Policy".
        </p>
      </div>
    </div>
  )
}


