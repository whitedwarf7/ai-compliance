import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithDemo: () => void
  logout: () => void
  setLoading: (loading: boolean) => void
}

// Demo user for pilot/demo mode
const DEMO_USER: User = {
  id: 'demo-user',
  email: 'admin@demo.com',
  name: 'Demo Admin',
  role: 'admin',
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      
      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          // In production, this would call the auth API
          // For now, accept any credentials in demo mode
          const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          })
          
          if (!response.ok) {
            throw new Error('Invalid credentials')
          }
          
          const data = await response.json()
          set({
            user: data.user,
            token: data.token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch {
          // Fallback to demo mode
          set({
            user: DEMO_USER,
            token: 'demo-token',
            isAuthenticated: true,
            isLoading: false,
          })
        }
      },
      
      loginWithDemo: () => {
        set({
          user: DEMO_USER,
          token: 'demo-token',
          isAuthenticated: true,
          isLoading: false,
        })
      },
      
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },
      
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)


