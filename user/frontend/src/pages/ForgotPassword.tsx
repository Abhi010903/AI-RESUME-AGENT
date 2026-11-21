import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Layers, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent } from '../components/ui/Card'

export const ForgotPassword: React.FC = () => {
  const [step, setStep] = useState<1 | 2>(1)
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const handleRequestToken = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const res = await api.auth.requestPasswordReset({ email })
      setSuccessMsg(res.message || 'If an account exists, a reset token has been generated.')
      if (res.reset_token) {
        setToken(res.reset_token)
      }
      setStep(2)
    } catch (err: any) {
      setError(err.message || 'Failed to request reset.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    setIsLoading(true)
    try {
      await api.auth.confirmPasswordReset({
        token,
        new_password: newPassword,
      })
      setSuccessMsg('Your password has been successfully reset! You can now log in.')
    } catch (err: any) {
      setError(err.message || 'Reset failed or token is expired.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 text-white mx-auto flex items-center justify-center shadow-lg">
            <Layers className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Password Recovery</h1>
          <p className="text-xs text-slate-400">Reset your candidate account password</p>
        </div>

        <Card className="border-slate-800 bg-white/95 backdrop-blur-sm shadow-2xl">
          <CardContent className="p-8">
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {successMsg && (
              <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            {step === 1 ? (
              <form onSubmit={handleRequestToken} className="space-y-4">
                <Input
                  label="Enter your account email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="candidate@example.com"
                  required
                />
                <Button type="submit" variant="primary" className="w-full" isLoading={isLoading}>
                  Send Reset Token <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </form>
            ) : (
              <form onSubmit={handleConfirmReset} className="space-y-4">
                <Input
                  label="Reset Token"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste token received"
                  required
                />
                <Input
                  label="New Password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  required
                />
                <Input
                  label="Confirm New Password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                <Button type="submit" variant="primary" className="w-full" isLoading={isLoading}>
                  Confirm New Password
                </Button>
              </form>
            )}

            <div className="mt-6 pt-6 border-t border-slate-100 text-center text-xs text-slate-500">
              Remember your password?{' '}
              <Link to="/login" className="font-semibold text-brand-600 hover:underline">
                Back to Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
