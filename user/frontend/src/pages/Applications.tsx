import React, { useEffect, useState } from 'react'
import {
  Kanban,
  Plus,
  Trash2,
  Edit2,
  Calendar,
  DollarSign,
  MapPin,
  ExternalLink,
  Search,
  AlertCircle,
  Clock,
  CheckCircle,
  FileText,
  Download,
  Briefcase,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'

export const STAGES = [
  'INTERESTED',
  'PREPARING',
  'APPLIED',
  'ASSESSMENT',
  'INTERVIEW',
  'OFFER',
  'REJECTED',
  'WITHDRAWN',
] as const

export const Applications: React.FC = () => {
  const [applications, setApplications] = useState<any[]>([])
  const [targetJobs, setTargetJobs] = useState<any[]>([])
  const [resumes, setResumes] = useState<any[]>([])

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modals
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingApp, setEditingApp] = useState<any | null>(null)

  // Form states
  const [form, setForm] = useState({
    job_id: '',
    resume_id: '',
    company: '',
    position_title: '',
    job_url: '',
    location: '',
    salary_range: '',
    status: 'INTERESTED',
    applied_date: new Date().toISOString().split('T')[0],
    notes: '',
  })

  const loadData = async () => {
    try {
      setIsLoading(true)
      const [apps, jbs, genResumes] = await Promise.all([
        api.applications.list(statusFilter || undefined, search || undefined),
        api.jobs.list(),
        api.generation.list(),
      ])
      setApplications(apps)
      setTargetJobs(jbs)
      setResumes(genResumes)
    } catch (err: any) {
      setError(err.message || 'Failed to load applications pipeline')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [search, statusFilter])

  const handleSelectJobForForm = (jobId: string) => {
    const job = targetJobs.find((j) => j.id === jobId)
    if (job) {
      setForm((prev) => ({
        ...prev,
        job_id: job.id,
        position_title: job.title,
        company: job.company || prev.company,
        location: job.location || prev.location,
      }))
    } else {
      setForm((prev) => ({ ...prev, job_id: '' }))
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.applications.create({
        ...form,
        job_id: form.job_id || undefined,
        resume_id: form.resume_id || undefined,
      })
      setShowAddModal(false)
      setForm({
        job_id: '',
        resume_id: '',
        company: '',
        position_title: '',
        job_url: '',
        location: '',
        salary_range: '',
        status: 'INTERESTED',
        applied_date: new Date().toISOString().split('T')[0],
        notes: '',
      })
      await loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to create application.')
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingApp) return
    try {
      await api.applications.update(editingApp.id, editingApp)
      setEditingApp(null)
      await loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to update application.')
    }
  }

  const handleMoveStage = async (id: string, newStatus: string) => {
    try {
      await api.applications.update(id, { status: newStatus })
      setApplications((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: newStatus } : a))
      )
    } catch (err: any) {
      alert(err.message || 'Failed to update stage.')
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this job application record from tracker?')) return
    try {
      await api.applications.delete(id)
      setApplications((prev) => prev.filter((a) => a.id !== id))
    } catch (err: any) {
      alert(err.message || 'Failed to delete application.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Job Application Tracker & Pipeline</h1>
          <p className="text-sm text-slate-500 mt-1">
            Organize your active job applications across 8 Kanban pipeline stages, linked to target jobs and generated resume versions.
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowAddModal(true)}>
          <Plus className="w-4 h-4" /> Track New Application
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search company or position title..."
            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Pipeline Stages ({applications.length})</option>
          {STAGES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* 8-Stage Kanban Pipeline Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3.5 overflow-x-auto pb-4">
        {STAGES.map((stage) => {
          const items = applications.filter((a) => a.status === stage)
          return (
            <div key={stage} className="bg-slate-100/70 rounded-xl p-3 flex flex-col min-w-[210px] border border-slate-200/60">
              <div className="flex items-center justify-between mb-3 px-1">
                <span className="text-[11px] font-bold text-slate-700 tracking-wider uppercase">{stage}</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white text-slate-600 shadow-xs border border-slate-200/50">
                  {items.length}
                </span>
              </div>

              <div className="space-y-3 flex-1">
                {items.length === 0 ? (
                  <div className="p-4 border-2 border-dashed border-slate-200 rounded-lg text-center text-slate-400 text-xs">
                    No positions
                  </div>
                ) : (
                  items.map((app) => (
                    <Card key={app.id} className="p-3.5 bg-white shadow-xs hover:shadow-md transition-shadow border-slate-200">
                      <div className="flex items-start justify-between gap-1">
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 leading-snug">{app.position_title}</h4>
                          <p className="text-[11px] font-medium text-brand-700 mt-0.5">{app.company}</p>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => setEditingApp(app)}
                            className="p-1 text-slate-400 hover:text-slate-600"
                            title="Edit"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => handleDelete(app.id)}
                            className="p-1 text-slate-400 hover:text-red-600"
                            title="Delete"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>

                      {/* Meta Pills */}
                      <div className="mt-2.5 space-y-1 text-[11px] text-slate-500">
                        {app.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3 h-3 text-slate-400" />
                            <span className="truncate">{app.location}</span>
                          </div>
                        )}
                        {app.salary_range && (
                          <div className="flex items-center gap-1">
                            <DollarSign className="w-3 h-3 text-slate-400" />
                            <span>{app.salary_range}</span>
                          </div>
                        )}
                        {app.applied_date && (
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-slate-400" />
                            <span>{app.applied_date}</span>
                          </div>
                        )}
                      </div>

                      {/* Resume / Job Links */}
                      {app.resume_id && (
                        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between">
                          <span className="text-[10px] text-brand-600 font-medium flex items-center gap-1">
                            <FileText className="w-3 h-3" /> Tailored Resume Linked
                          </span>
                          <a
                            href={api.generation.downloadUrl(app.resume_id, 'pdf')}
                            target="_blank"
                            rel="noreferrer"
                            className="text-slate-400 hover:text-brand-600"
                            title="Download PDF"
                          >
                            <Download className="w-3 h-3" />
                          </a>
                        </div>
                      )}

                      {/* Move Stage Selector */}
                      <div className="mt-3 pt-2 border-t border-slate-100">
                        <select
                          value={app.status}
                          onChange={(e) => handleMoveStage(app.id, e.target.value)}
                          className="w-full text-[10px] py-1 px-1.5 rounded border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
                        >
                          {STAGES.map((s) => (
                            <option key={s} value={s}>Move: {s}</option>
                          ))}
                        </select>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Add Application Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Track New Job Application"
        description="Add a target position to your application pipeline, linking target job requirements and tailored resumes."
      >
        <form onSubmit={handleCreate} className="space-y-4">
          {targetJobs.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Pre-fill from Target Job (Optional)</label>
              <select
                value={form.job_id}
                onChange={(e) => handleSelectJobForForm(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2 bg-white"
              >
                <option value="">Select an analyzed job...</option>
                {targetJobs.map((j) => (
                  <option key={j.id} value={j.id}>{j.title} at {j.company || 'Company'}</option>
                ))}
              </select>
            </div>
          )}

          {resumes.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Link Tailored Resume Version (Optional)</label>
              <select
                value={form.resume_id}
                onChange={(e) => setForm({ ...form, resume_id: e.target.value })}
                className="w-full text-xs rounded-lg border border-slate-300 p-2 bg-white"
              >
                <option value="">None (or upload later)</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>{r.title} (v{r.version_number})</option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Company Name"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
              required
            />
            <Input
              label="Position Title"
              value={form.position_title}
              onChange={(e) => setForm({ ...form, position_title: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Location"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              placeholder="e.g. Remote, San Francisco, CA"
            />
            <Input
              label="Salary Range"
              value={form.salary_range}
              onChange={(e) => setForm({ ...form, salary_range: e.target.value })}
              placeholder="e.g. $140,000 - $170,000"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Pipeline Stage</label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full text-xs rounded-lg border border-slate-300 p-2 bg-white"
              >
                {STAGES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <Input
              label="Application Date"
              type="date"
              value={form.applied_date}
              onChange={(e) => setForm({ ...form, applied_date: e.target.value })}
            />
          </div>

          <Input
            label="Job Posting URL"
            value={form.job_url}
            onChange={(e) => setForm({ ...form, job_url: e.target.value })}
            placeholder="https://..."
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Application Notes / Contacts</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={3}
              className="w-full rounded-lg border border-slate-300 p-2 text-xs focus:ring-2 focus:ring-brand-500"
              placeholder="Notes on recruiters, interviewers, referrals, or key questions..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Create Application
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Application Modal */}
      {editingApp && (
        <Modal
          isOpen={true}
          onClose={() => setEditingApp(null)}
          title={`Edit Application: ${editingApp.position_title}`}
          description={`Update details for position at ${editingApp.company}`}
        >
          <form onSubmit={handleUpdate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Company Name"
                value={editingApp.company}
                onChange={(e) => setEditingApp({ ...editingApp, company: e.target.value })}
                required
              />
              <Input
                label="Position Title"
                value={editingApp.position_title}
                onChange={(e) => setEditingApp({ ...editingApp, position_title: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Pipeline Stage</label>
                <select
                  value={editingApp.status}
                  onChange={(e) => setEditingApp({ ...editingApp, status: e.target.value })}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2 bg-white"
                >
                  {STAGES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <Input
                label="Application Date"
                type="date"
                value={editingApp.applied_date || ''}
                onChange={(e) => setEditingApp({ ...editingApp, applied_date: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Location"
                value={editingApp.location || ''}
                onChange={(e) => setEditingApp({ ...editingApp, location: e.target.value })}
              />
              <Input
                label="Salary Range"
                value={editingApp.salary_range || ''}
                onChange={(e) => setEditingApp({ ...editingApp, salary_range: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Notes</label>
              <textarea
                value={editingApp.notes || ''}
                onChange={(e) => setEditingApp({ ...editingApp, notes: e.target.value })}
                rows={3}
                className="w-full rounded-lg border border-slate-300 p-2 text-xs focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setEditingApp(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                Save Changes
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
