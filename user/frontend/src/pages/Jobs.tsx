import React, { useEffect, useState, useRef } from 'react'
import {
  Briefcase,
  Plus,
  Upload,
  FileText,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Eye,
  ExternalLink,
  Sparkles,
  MapPin,
  Clock,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'

export const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Modals
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedJob, setSelectedJob] = useState<any | null>(null)
  const [activeTab, setActiveTab] = useState<'text' | 'file'>('text')

  // Form states
  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [location, setLocation] = useState('')
  const [rawText, setRawText] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  const loadJobs = async () => {
    try {
      setIsLoading(true)
      const data = await api.jobs.list()
      setJobs(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load jobs')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadJobs()
  }, [])

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)
    setIsSubmitting(true)

    try {
      if (activeTab === 'file') {
        if (!uploadedFile) {
          throw new Error('Please select a file to upload.')
        }
        await api.jobs.upload(uploadedFile, { title, company, location })
      } else {
        if (!rawText.trim()) {
          throw new Error('Please paste the job description text.')
        }
        await api.jobs.analyze(rawText, { title, company, location })
      }

      setSuccessMsg('Job description successfully analyzed and requirements extracted.')
      setShowAddModal(false)
      setTitle('')
      setCompany('')
      setLocation('')
      setRawText('')
      setUploadedFile(null)
      await loadJobs()
    } catch (err: any) {
      setError(err.message || 'Failed to analyze job.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteJob = async (id: string) => {
    if (!window.confirm('Delete this job description?')) return
    try {
      await api.jobs.delete(id)
      setJobs((prev) => prev.filter((j) => j.id !== id))
      if (selectedJob?.id === id) setSelectedJob(null)
    } catch (err: any) {
      setError(err.message || 'Failed to delete job.')
    }
  }

  const handleViewDetails = async (job: any) => {
    try {
      const fullJob = await api.jobs.get(job.id)
      setSelectedJob(fullJob)
    } catch {
      setSelectedJob(job)
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Job Description Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Upload or paste target job postings to automatically extract mandatory requirements, preferred skills, and ATS criteria.
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowAddModal(true)}>
          <Plus className="w-4 h-4" /> Add Target Job
        </Button>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center gap-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Job Cards Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Loading analyzed jobs...</div>
      ) : jobs.length === 0 ? (
        <Card className="text-center p-12">
          <Briefcase className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-900">No Target Jobs Added</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto mt-2">
            Add job descriptions that you wish to target. Our parser will extract required competencies for skill matching and resume tailoring.
          </p>
          <Button variant="primary" className="mt-6" onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4" /> Add First Job
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {jobs.map((job) => (
            <Card key={job.id} className="hover:border-brand-200 transition-all flex flex-col justify-between">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 line-clamp-1">{job.title}</h3>
                    <p className="text-xs font-medium text-brand-700 mt-0.5">{job.company || 'Unknown Company'}</p>
                  </div>
                  <Badge variant="brand" className="uppercase text-[10px]">
                    {job.seniority_level || 'Any level'}
                  </Badge>
                </div>

                {job.location && (
                  <p className="text-xs text-slate-400 flex items-center gap-1 mt-2">
                    <MapPin className="w-3 h-3" /> {job.location}
                  </p>
                )}

                {job.summary && (
                  <p className="text-xs text-slate-600 line-clamp-3 mt-3 leading-relaxed">
                    {job.summary}
                  </p>
                )}

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span>Req. Skills: <strong>{job.required_skills?.length || 0}</strong></span>
                  <span>Pref. Skills: <strong>{job.preferred_skills?.length || 0}</strong></span>
                  {job.min_years_experience !== null && (
                    <span>Min: <strong>{job.min_years_experience}y</strong></span>
                  )}
                </div>
              </CardContent>

              <div className="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={() => handleViewDetails(job)}
                  className="text-xs text-brand-600 font-semibold hover:underline flex items-center gap-1"
                >
                  <Eye className="w-3.5 h-3.5" /> Inspect Requirements
                </button>
                <button
                  onClick={() => handleDeleteJob(job.id)}
                  className="p-1 text-slate-400 hover:text-red-600 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Job Modal */}
      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add Target Job Description" maxWidth="xl">
        <form onSubmit={handleCreateJob} className="space-y-4">
          <div className="flex border-b border-slate-200 mb-4">
            <button
              type="button"
              onClick={() => setActiveTab('text')}
              className={`pb-2 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'text' ? 'border-brand-600 text-brand-600' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Paste JD Text
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('file')}
              className={`pb-2 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'file' ? 'border-brand-600 text-brand-600' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Upload Document (.pdf, .docx, .txt, .md)
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Input label="Position Title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. AI Engineer" />
            <Input label="Company (optional)" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Stripe" />
            <Input label="Location (optional)" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Remote / NYC" />
          </div>

          {activeTab === 'text' ? (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Raw Job Description Text</label>
              <textarea
                rows={8}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Paste the full job posting including responsibilities, requirements, and qualifications..."
                className="w-full rounded-lg border border-slate-300 p-3 text-sm focus:ring-2 focus:ring-brand-500 font-sans"
                required
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Select File</label>
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-xl p-6 text-center cursor-pointer bg-slate-50/50"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <Upload className="w-8 h-8 text-brand-600 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-800">
                  {uploadedFile ? uploadedFile.name : 'Click to select job file'}
                </p>
                <p className="text-xs text-slate-500 mt-1">PDF, DOCX, TXT, or MD format</p>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowAddModal(false)}>Cancel</Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              <Sparkles className="w-4 h-4" /> Analyze & Extract
            </Button>
          </div>
        </form>
      </Modal>

      {/* View Job Details Modal */}
      <Modal
        isOpen={selectedJob !== null}
        onClose={() => setSelectedJob(null)}
        title={selectedJob?.title || 'Job Details'}
        description={`${selectedJob?.company || 'Company'} • ${selectedJob?.location || 'Location'}`}
        maxWidth="2xl"
      >
        {selectedJob && (
          <div className="space-y-6">
            {/* Required Skills */}
            <div>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                Mandatory Technical Skills ({selectedJob.required_skills?.length || 0})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {selectedJob.required_skills?.map((s: any, idx: number) => (
                  <Badge key={idx} variant="brand" className="text-xs">
                    {typeof s === 'string' ? s : s.name}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Preferred Skills */}
            {selectedJob.preferred_skills?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Preferred / Nice-to-have Skills ({selectedJob.preferred_skills.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedJob.preferred_skills.map((s: any, idx: number) => (
                    <Badge key={idx} variant="neutral" className="text-xs">
                      {typeof s === 'string' ? s : s.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Responsibilities */}
            {selectedJob.responsibilities?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Core Responsibilities</h4>
                <ul className="list-disc list-inside text-xs text-slate-600 space-y-1">
                  {selectedJob.responsibilities.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Required Qualifications */}
            {selectedJob.required_qualifications?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Required Qualifications</h4>
                <ul className="list-disc list-inside text-xs text-slate-600 space-y-1">
                  {selectedJob.required_qualifications.map((q: string, idx: number) => (
                    <li key={idx}>{q}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Quality Warnings */}
            {selectedJob.quality_warnings?.length > 0 && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
                <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" /> JD Quality Observations
                </h4>
                <ul className="list-disc list-inside text-xs text-amber-700 space-y-0.5">
                  {selectedJob.quality_warnings.map((w: string, idx: number) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
