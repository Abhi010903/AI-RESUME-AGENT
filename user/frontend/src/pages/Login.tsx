import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Layers, ArrowRight, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent } from '../components/ui/Card'

export const Login: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const res = await api.auth.login({ email, password })
      login(res.access_token)
      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Invalid email or password.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 text-white mx-auto flex items-center justify-center shadow-lg">
            <Layers className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Resume Agent</h1>
          <p className="text-xs text-slate-400">Sign in to your candidate intelligence platform</p>
        </div>

        <Card className="border-slate-800 bg-white/95 backdrop-blur-sm shadow-2xl">
          <CardContent className="p-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <Input
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="candidate@example.com"
                required
              />

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-slate-700">Password</label>
                  <Link to="/forgot-password" className="text-xs text-brand-600 hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
                Sign In <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </form>

            <div className="mt-6 pt-6 border-t border-slate-100 text-center text-xs text-slate-500">
              Don't have an account?{' '}
              <Link to="/register" className="font-semibold text-brand-600 hover:underline">
                Create candidate account
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
