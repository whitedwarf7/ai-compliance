export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'analyst' | 'viewer'
  avatar?: string
}

export interface AuditLog {
  id: string
  org_id: string
  app_id: string
  user_id: string | null
  model: string
  provider: string
  prompt_hash: string
  token_count_input: number | null
  token_count_output: number | null
  latency_ms: number | null
  risk_flags: string[]
  metadata: Record<string, unknown>
  created_at: string
}

export interface Violation {
  id: string
  org_id: string
  app_id: string
  user_id: string | null
  model: string
  risk_flags: string[]
  action: 'blocked' | 'masked' | 'warned' | 'allowed'
  created_at: string
}

export interface ViolationSummary {
  total_violations: number
  total_blocked: number
  total_masked: number
  total_warned: number
  by_type: Record<string, number>
  by_action: Record<string, number>
  by_severity: Record<string, number>
  top_violating_apps: Array<{ app_id: string; violation_count: number }>
  top_violating_orgs: Array<{ org_id: string; violation_count: number }>
  recent_violations: Violation[]
}

export interface LogStats {
  total_requests: number
  total_tokens_input: number
  total_tokens_output: number
  unique_models: number
  unique_apps: number
  requests_with_risk_flags: number
}

export interface Policy {
  version: string
  name: string
  description: string
  rules: PolicyRules
}

export interface PolicyRules {
  block_if: string[]
  mask_if: string[]
  warn_if: string[]
  allowed_models: string[]
  blocked_models: string[]
  allowed_apps: string[]
  blocked_apps: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface ViolationTrend {
  date: string
  total: number
  blocked: number
  masked: number
  warned: number
}


