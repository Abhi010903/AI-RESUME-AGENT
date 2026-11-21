import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  User,
  Key,
  Trash2,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  Save,
} from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'

export const Settings: React.FC = () => {
  const { user, refreshUser, logout } = useAuth()
  const navigate = useNavigate()

  // Profile Update Form
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false)

  // Password Change Form
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [pwSuccess, setPwSuccess] = useState<string | null>(null)
  const [pwError, setPwError] = useState<string | null>(null)
  const [isChangingPw, setIsChangingPw] = useState(false)

  // Delete Account
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileSuccess(null)
    setProfileError(null)
    setIsUpdatingProfile(true)
    try {
      await api.auth.updateMe({ full_name: fullName })
      await refreshUser()
      setProfileSuccess('Profile updated successfully.')
    } catch (err: any) {
      setProfileError(err.message || 'Failed to update profile.')
    } finally {
      setIsUpdatingProfile(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwSuccess(null)
    setPwError(null)

    if (newPassword !== confirmPassword) {
      setPwError('New passwords do not match.')
      return
    }

    if (newPassword.length < 8) {
      setPwError('New password must be at least 8 characters long.')
      return
    }

    setIsChangingPw(true)
    try {
      await api.auth.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setPwSuccess('Password changed successfully.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: any) {
      setPwError(err.message || 'Failed to change password.')
    } finally {
      setIsChangingPw(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') return
    setIsDeleting(true)
    try {
      await api.auth.deleteAccount()
      logout()
      navigate('/login')
    } catch (err: any) {
      alert(err.message || 'Failed to delete account.')
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Account Settings & Security</h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage your candidate credentials, update personal details, and configure account security.
        </p>
      </div>

      {/* Profile Details Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <User className="w-4 h-4 text-brand-600" /> Personal Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpdateProfile} className="space-y-4">
            {profileSuccess && (
              <div className="p-3 rounded-lg bg-emerald-50 text-emerald-700 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{profileSuccess}</span>
              </div>
            )}
            {profileError && (
              <div className="p-3 rounded-lg bg-red-50 text-red-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{profileError}</span>
              </div>
            )}

            <Input
              label="Email Address"
              value={user?.email || ''}
              disabled
              helperText="Email cannot be changed."
            />
            <Input
              label="Full Legal Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />

            <div className="flex justify-end">
              <Button type="submit" variant="primary" size="sm" isLoading={isUpdatingProfile}>
                <Save className="w-3.5 h-3.5" /> Save Name
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Password Change Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Key className="w-4 h-4 text-brand-600" /> Change Password
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            {pwSuccess && (
              <div className="p-3 rounded-lg bg-emerald-50 text-emerald-700 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{pwSuccess}</span>
              </div>
            )}
            {pwError && (
              <div className="p-3 rounded-lg bg-red-50 text-red-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{pwError}</span>
              </div>
            )}

            <Input
              label="Current Password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            </div>

            <div className="flex justify-end">
              <Button type="submit" variant="primary" size="sm" isLoading={isChangingPw}>
                Update Password
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Application Preferences Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-brand-600" /> Application Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Default Document Export Format</label>
              <select className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white">
                <option value="pdf">Single-Page A4 PDF (Recommended)</option>
                <option value="docx">Microsoft Word DOCX</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Default Resume Template</label>
              <select className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white">
                <option value="classic">Classic Clean (Single Column A4)</option>
                <option value="modern">Modern Professional</option>
              </select>
            </div>
          </div>
          <p className="text-xs text-slate-500">
            Preferences automatically apply when tailoring new resume versions.
          </p>
        </CardContent>
      </Card>

      {/* Privacy & Data Governance Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Save className="w-4 h-4 text-brand-600" /> Data Governance & Portability
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Export Complete Career Knowledge Base</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-md">
                Download a complete JSON export of your candidate account, verified profile claims, extracted resume facts, target jobs, applications, and activity history.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                try {
                  const data = await api.auth.exportData()
                  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `career_data_export_${new Date().toISOString().split('T')[0]}.json`
                  document.body.appendChild(a)
                  a.click()
                  document.body.removeChild(a)
                  URL.revokeObjectURL(url)
                } catch (err: any) {
                  alert(err.message || 'Failed to export candidate data')
                }
              }}
              className="flex-shrink-0"
            >
              Export Data (JSON)
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone: Account Deletion */}
      <Card className="border-red-200">
        <CardHeader className="bg-red-50/50">
          <CardTitle className="text-base font-semibold text-red-700 flex items-center gap-2">
            <Trash2 className="w-4 h-4 text-red-600" /> Danger Zone
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Delete Candidate Account</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-md">
                Permanently deletes your user account, uploaded resumes, profile evidence, and generated resume documents. This action cannot be reversed.
              </p>
            </div>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowDeleteModal(true)}
              className="flex-shrink-0"
            >
              Delete Account
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Confirm Account Deletion"
        description="Please confirm that you want to delete your entire candidate platform account."
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-800 text-xs">
            <p className="font-semibold">Warning: Irreversible Action</p>
            <p className="mt-1">
              All stored resumes, consolidated profile facts, match analyses, and generated documents will be purged immediately.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Type <strong className="text-red-600">DELETE</strong> to confirm:
            </label>
            <Input
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="DELETE"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
            <Button
              variant="danger"
              disabled={deleteConfirmText !== 'DELETE'}
              isLoading={isDeleting}
              onClick={handleDeleteAccount}
            >
              Permanently Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
