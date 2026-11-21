import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AppLayout } from './components/layout/AppLayout'

// Pages
import { Dashboard } from './pages/Dashboard'
import { Resumes } from './pages/Resumes'
import { Profile } from './pages/Profile'
import { Jobs } from './pages/Jobs'
import { Matching } from './pages/Matching'
import { Generation } from './pages/Generation'
import { AtsEvaluation } from './pages/AtsEvaluation'
import { Applications } from './pages/Applications'
import { Settings } from './pages/Settings'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { ForgotPassword } from './pages/ForgotPassword'

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-900 text-slate-400 text-sm">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <span>Authenticating candidate session...</span>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* Protected Candidate Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="resumes" element={<Resumes />} />
            <Route path="profile" element={<Profile />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="matching" element={<Matching />} />
            <Route path="generation" element={<Generation />} />
            <Route path="ats" element={<AtsEvaluation />} />
            <Route path="applications" element={<Applications />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
