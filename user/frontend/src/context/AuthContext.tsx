import React, { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../services/api'

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_verified: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string, user?: User) => void
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user')
    return saved ? JSON.parse(saved) : null
  })
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = async () => {
    try {
      if (!token) {
        setUser(null)
        setIsLoading(false)
        return
      }
      const data = await api.auth.getMe()
      setUser(data)
      localStorage.setItem('user', JSON.stringify(data))
    } catch {
      logout()
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (token) {
      refreshUser()
    } else {
      setIsLoading(false)
    }
  }, [token])

  const login = (newToken: string, newUser?: User) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
    if (newUser) {
      setUser(newUser)
      localStorage.setItem('user', JSON.stringify(newUser))
    } else {
      refreshUser()
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    try {
      api.auth.logout().catch(() => {})
    } catch {}
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
