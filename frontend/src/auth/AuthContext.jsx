import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { getCurrentAdmin, loginAdmin, setAuthToken } from '../services/api'

const STORAGE_KEY = 'smartphone-dashboard-admin-token'
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY))
  const [currentAdmin, setCurrentAdmin] = useState(null)
  const [loading, setLoading] = useState(Boolean(token))

  useEffect(() => {
    setAuthToken(token)
    if (!token) {
      setCurrentAdmin(null)
      setLoading(false)
      return
    }
    setLoading(true)
    getCurrentAdmin()
      .then(setCurrentAdmin)
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY)
        setAuthToken(null)
        setToken(null)
        setCurrentAdmin(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const value = useMemo(() => ({
    token,
    currentAdmin,
    loading,
    isAuthenticated: Boolean(token && currentAdmin),
    async login(email, password) {
      const result = await loginAdmin(email, password)
      localStorage.setItem(STORAGE_KEY, result.access_token)
      setAuthToken(result.access_token)
      setToken(result.access_token)
      setCurrentAdmin(result.admin)
      return result.admin
    },
    logout() {
      localStorage.removeItem(STORAGE_KEY)
      setAuthToken(null)
      setToken(null)
      setCurrentAdmin(null)
    },
  }), [token, currentAdmin, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
