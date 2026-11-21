import React, { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload,
  FileText,
  Trash2,
  Eye,
  RefreshCw,
  Download,
  AlertCircle,
  CheckCircle2,
  Layers,
  ArrowRight,
  Search,
  Filter,
  AlertTriangle,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'

export const Resumes: React.FC = () => {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [resumes, setResumes] = useState<any[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isConsolidating, setIsConsolidating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Preview modal
  const [previewDoc, setPreviewDoc] = useState<any | null>(null)
  const [previewTab, setPreviewTab] = useState<'text' | 'warnings'>('text')
  const [isLoadingText, setIsLoadingText] = useState(false)

  const loadResumes = async () => {
    try {
      setIsLoading(true)
      const data = await api.resumes.list()
      setResumes(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch uploaded resumes')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadResumes()
  }, [])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setError(null)
    setSuccessMsg(null)
    setIsUploading(true)

    try {
      const fileList = Array.from(files)
      if (fileList.length > 10) {
        throw new Error('Maximum 10 resumes can be uploaded in one batch.')
      }

      await api.resumes.uploadBatch(fileList)
      setSuccessMsg(`Successfully uploaded and parsed ${fileList.length} resume(s).`)
      await loadResumes()
    } catch (err: any) {
      setError(err.message || 'Error uploading files.')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this resume document? Verified claims in consolidated profiles will be preserved.')) return
    try {
      await api.resumes.delete(id)
      setResumes((prev) => prev.filter((r) => r.id !== id))
      setSelectedIds((prev) => prev.filter((item) => item !== id))
      setSuccessMsg('Resume deleted successfully.')
    } catch (err: any) {
      setError(err.message || 'Failed to delete resume.')
    }
  }

  const handleReprocess = async (id: string) => {
    try {
      await api.resumes.reprocess(id)
      await loadResumes()
      setSuccessMsg('Extraction reprocessed successfully.')
    } catch (err: any) {
      setError(err.message || 'Reprocessing failed.')
    }
  }

  const handleOpenPreview = async (doc: any) => {
    setIsLoadingText(true)
    setPreviewDoc(doc)
    setPreviewTab('text')
    try {
      const res = await api.resumes.getText(doc.id)
      setPreviewDoc({ ...doc, extracted_text: res.extracted_text, warnings: res.warnings || [] })
    } catch (err: any) {
      setPreviewDoc({ ...doc, extracted_text: `Error loading extracted text: ${err.message}`, warnings: [] })
    } finally {
      setIsLoadingText(false)
    }
  }

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    )
  }

  const handleConsolidate = async () => {
    if (selectedIds.length === 0) {
      setError('Please select at least 1 completed resume to consolidate.')
      return
    }

    setIsConsolidating(true)
    setError(null)
    try {
      await api.profiles.consolidate(selectedIds)
      navigate('/profile')
    } catch (err: any) {
      setError(err.message || 'Consolidation failed.')
      setIsConsolidating(false)
    }
  }

  const filteredResumes = resumes.filter((r) => {
    const matchesSearch = r.filename.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'ALL' || r.status.toUpperCase() === statusFilter.toUpperCase()
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Resume Ingestion & Extraction</h1>
          <p className="text-sm text-slate-500 mt-1">
            Upload PDF or DOCX resumes. The ingestion engine parses layout, preserves headings, and extracts career evidence.
          </p>
        </div>
        {selectedIds.length > 0 && (
          <Button
            variant="primary"
            onClick={handleConsolidate}
            isLoading={isConsolidating}
            className="shadow-md"
          >
            <Layers className="w-4 h-4" />
            Consolidate {selectedIds.length} Selected Resume(s) into Master Profile
          </Button>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Upload Dropzone Card */}
      <Card>
        <CardContent className="p-8">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-50/50 hover:bg-brand-50/20"
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="w-14 h-14 rounded-2xl bg-brand-100 text-brand-600 flex items-center justify-center mb-4 shadow-sm">
              <Upload className="w-7 h-7" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">
              {isUploading ? 'Uploading and parsing documents...' : 'Click or drag resumes to upload'}
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Supports batch upload of up to 10 PDF and DOCX files (up to 10MB each) with magic byte verification.
            </p>
            <Button variant="outline" size="sm" className="mt-4 pointer-events-none" isLoading={isUploading}>
              Browse Local Files
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Resumes Library with Search & Filtering */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100">
          <div>
            <CardTitle className="text-base font-semibold">Resume Documents Library</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Select one or multiple resumes to consolidate into your unified candidate profile.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search filename..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 w-44"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="py-1.5 px-2.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
            >
              <option value="ALL">All Statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="PENDING">Processing</option>
              <option value="FAILED">Failed</option>
            </select>

            <Button variant="ghost" size="sm" onClick={loadResumes} disabled={isLoading}>
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-12 text-center text-slate-500 text-sm">Loading resume library...</div>
          ) : filteredResumes.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-sm">
              {resumes.length === 0
                ? 'No resumes uploaded yet. Upload your current CV to get started.'
                : 'No resumes matching the current filters.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <tr>
                    <th className="p-4 w-12 text-center">
                      <input
                        type="checkbox"
                        checked={filteredResumes.length > 0 && selectedIds.length === filteredResumes.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedIds(filteredResumes.map((r) => r.id))
                          } else {
                            setSelectedIds([])
                          }
                        }}
                        className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                      />
                    </th>
                    <th className="p-4">Document</th>
                    <th className="p-4">Format</th>
                    <th className="p-4">Size</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Pages</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredResumes.map((resume) => {
                    const isSelected = selectedIds.includes(resume.id)
                    return (
                      <tr
                        key={resume.id}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          isSelected ? 'bg-brand-50/40' : ''
                        }`}
                      >
                        <td className="p-4 text-center">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelect(resume.id)}
                            className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                          />
                        </td>
                        <td className="p-4 font-medium text-slate-900">
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-slate-400 flex-shrink-0" />
                            <div>
                              <span className="truncate max-w-xs block font-semibold">{resume.filename}</span>
                              <span className="text-[10px] text-slate-400">ID: {resume.id.slice(0, 8)}</span>
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge variant="neutral" className="uppercase font-mono text-[11px]">
                            {resume.file_format}
                          </Badge>
                        </td>
                        <td className="p-4 text-slate-500 text-xs">
                          {(resume.file_size / 1024).toFixed(1)} KB
                        </td>
                        <td className="p-4">
                          <Badge
                            variant={
                              resume.status === 'completed'
                                ? 'success'
                                : resume.status === 'failed'
                                ? 'error'
                                : 'warning'
                            }
                          >
                            {resume.status}
                          </Badge>
                        </td>
                        <td className="p-4 text-slate-600 text-xs">{resume.page_count ?? '—'}</td>
                        <td className="p-4 text-right space-x-1">
                          <button
                            onClick={() => handleOpenPreview(resume)}
                            className="p-1.5 text-slate-400 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Preview Extracted Content"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <a
                            href={api.resumes.downloadUrl(resume.id)}
                            target="_blank"
                            rel="noreferrer"
                            className="p-1.5 inline-block text-slate-400 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Download Original File"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                          <button
                            onClick={() => handleReprocess(resume.id)}
                            className="p-1.5 text-slate-400 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Reprocess Extraction"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(resume.id)}
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dual Panel Preview Modal */}
      <Modal
        isOpen={previewDoc !== null}
        onClose={() => setPreviewDoc(null)}
        title={`Document Inspection: ${previewDoc?.filename}`}
        description="Inspect structured text extraction and layout parsing warnings."
        maxWidth="2xl"
      >
        {isLoadingText ? (
          <div className="py-8 text-center text-slate-500 text-sm">Loading extraction...</div>
        ) : (
          <div className="space-y-4">
            <div className="flex border-b border-slate-200 gap-4 text-xs font-semibold">
              <button
                onClick={() => setPreviewTab('text')}
                className={`pb-2 border-b-2 transition-colors ${
                  previewTab === 'text'
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Extracted Text
              </button>
              <button
                onClick={() => setPreviewTab('warnings')}
                className={`pb-2 border-b-2 transition-colors ${
                  previewTab === 'warnings'
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Extraction Warnings ({previewDoc?.warnings?.length || 0})
              </button>
            </div>

            {previewTab === 'text' ? (
              <pre className="p-4 bg-slate-900 text-slate-200 rounded-xl text-xs font-mono whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
                {previewDoc?.extracted_text || 'No text extracted.'}
              </pre>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {(!previewDoc?.warnings || previewDoc?.warnings?.length === 0) ? (
                  <p className="text-xs text-slate-500 p-4 text-center">No parsing warnings. Clean extraction.</p>
                ) : (
                  previewDoc.warnings.map((w: string, idx: number) => (
                    <div key={idx} className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
