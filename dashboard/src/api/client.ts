import axios from 'axios'
import { useAuthStore } from '../store/auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

// API functions
export const api = {
  // Audit logs
  getLogs: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/api/v1/logs', { params })
    return response.data
  },
  
  getLogStats: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/api/v1/logs/stats', { params })
    return response.data
  },
  
  exportLogsCSV: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/api/v1/logs/export/csv', {
      params,
      responseType: 'blob',
    })
    return response.data
  },
  
  // Violations
  getViolations: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/api/v1/violations', { params })
    return response.data
  },
  
  getViolationsSummary: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get('/api/v1/violations/summary', { params })
    return response.data
  },
  
  getViolationsTrends: async (days = 30) => {
    const response = await apiClient.get('/api/v1/violations/trends', { params: { days } })
    return response.data
  },
  
  getViolationsByType: async () => {
    const response = await apiClient.get('/api/v1/violations/by-type')
    return response.data
  },
  
  // Policy
  getPolicy: async () => {
    const response = await apiClient.get('/v1/policy')
    return response.data
  },
  
  reloadPolicy: async () => {
    const response = await apiClient.post('/v1/policy/reload')
    return response.data
  },
}

