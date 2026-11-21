import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Wand2,
  Download,
  FileText,
  Trash2,
  Eye,
  CheckCircle2,
  Clock,
  Sparkles,
  GitBranch,
  ShieldCheck,
  ExternalLink,
  AlertCircle,
  Layers,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'

export const Generation: React.FC = () => {
  const [searchParams] = useSearchParams()

  const [profiles, setProfiles] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [generatedList, setGeneratedList] = useState<any[]>([])

  const [selectedProfileId, setSelectedProfileId] = useState('')
  const [selectedJobId, setSelectedJobId] = useState('')
  const [customTitle, setCustomTitle] = useState('')

  const [activeResume, setActiveResume] = useState<any | null>(null)
  const [versionDiff, setVersionDiff] = useState<any | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [showProvenanceModal, setShowProvenanceModal] = useState(false)
  const [showVersionModal, setShowVersionModal] = useState(false)

  const loadData = async () => {
    try {
      setIsLoading(true)
      const [profs, jbs, genList] = await Promise.all([
        api.profiles.list(),
        api.jobs.list(),
        api.generation.list(),
      ])
      setProfiles(profs)
      setJobs(jbs)
      setGeneratedList(genList)

      const qProf = searchParams.get('profile_id')
      const qJob = searchParams.get('job_id')

      if (qProf) setSelectedProfileId(qProf)
      else if (profs.length > 0) setSelectedProfileId(profs[0].id)

      if (qJob) setSelectedJobId(qJob)
      else if (jbs.length > 0) setSelectedJobId(jbs[0].id)

      if (genList.length > 0 && !activeResume) {
        const first = await api.generation.get(genList[0].id)
        setActiveResume(first)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load generation data')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [searchParams])

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedProfileId || !selectedJobId) {
      setError('Please select both a candidate profile and a target job.')
      return
    }

    setIsGenerating(true)
    setError(null)
    try {
      const matchId = searchParams.get('match_id') || undefined
      const newResume = await api.generation.generate({
        profile_id: selectedProfileId,
        job_id: selectedJobId,
        match_id: matchId,
        title: customTitle || undefined,
      })
      setActiveResume(newResume)
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Generation failed.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDeleteGenerated = async (id: string) => {
    if (!window.confirm('Delete this generated resume?')) return
    try {
      await api.generation.delete(id)
      setGeneratedList((prev) => prev.filter((r) => r.id !== id))
      if (activeResume?.id === id) setActiveResume(null)
    } catch (err: any) {
      setError(err.message || 'Failed to delete resume.')
    }
  }

  const handleInspectVersions = async (id: string) => {
    try {
      const diff = await api.generation.getVersions(id)
      setVersionDiff(diff)
      setShowVersionModal(true)
    } catch (err: any) {
      alert(err.message || 'Failed to fetch version comparison.')
    }
  }

  const selectResumeToView = async (id: string) => {
    try {
      const full = await api.generation.get(id)
      setActiveResume(full)
    } catch (err: any) {
      alert(err.message || 'Failed to view resume.')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">ATS Resume Builder & Document Export</h1>
        <p className="text-sm text-slate-500 mt-1">
          Generate factually backed, single-page, A4-compliant resumes in DOCX and PDF with claim-level provenance tracking.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Generation Wizard Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-600" /> Tailor Resume to Job Requirements
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleGenerate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Candidate Profile</label>
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2 text-sm bg-white focus:ring-2 focus:ring-brand-500"
                  required
                >
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>{p.full_name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Target Role / Job</label>
                <select
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2 text-sm bg-white focus:ring-2 focus:ring-brand-500"
                  required
                >
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>{j.title} ({j.company || 'Role'})</option>
                  ))}
                </select>
              </div>

              <div>
                <Input
                  label="Custom Resume Title (optional)"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="e.g. Senior AI Engineer - DeepMind"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" variant="primary" isLoading={isGenerating} className="shadow-md">
                <Wand2 className="w-4 h-4" /> Generate Single-Page Resume (PDF & DOCX)
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Active Resume Preview & Provenance */}
      {activeResume && (
        <Card className="border-brand-200 shadow-md">
          <CardHeader className="bg-slate-50/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <CardTitle className="text-lg font-bold text-slate-900">{activeResume.title}</CardTitle>
                <Badge variant="brand" className="text-xs">v{activeResume.version_number}</Badge>
                {activeResume.ats_score !== undefined && (
                  <Badge variant="success" className="text-xs">
                    {activeResume.ats_score.toFixed(0)} ATS Score
                  </Badge>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Target Role: <strong>{activeResume.target_role}</strong> {activeResume.target_company ? `at ${activeResume.target_company}` : ''}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowProvenanceModal(true)}
              >
                <ShieldCheck className="w-3.5 h-3.5 text-brand-600" /> Provenance Inspector
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleInspectVersions(activeResume.id)}
              >
                <GitBranch className="w-3.5 h-3.5" /> Version History
              </Button>
              <a
                href={api.generation.downloadUrl(activeResume.id, 'docx')}
                target="_blank"
                rel="noreferrer"
              >
                <Button variant="outline" size="sm">
                  <Download className="w-3.5 h-3.5" /> DOCX
                </Button>
              </a>
              <a
                href={api.generation.downloadUrl(activeResume.id, 'pdf')}
                target="_blank"
                rel="noreferrer"
              >
                <Button variant="primary" size="sm" className="shadow-sm">
                  <Download className="w-3.5 h-3.5" /> Download PDF
                </Button>
              </a>
            </div>
          </CardHeader>

          {/* Structured Document Preview */}
          <CardContent className="p-8 bg-white space-y-6 max-w-4xl mx-auto border-x border-slate-100 my-4 shadow-sm rounded-lg">
            {/* Header */}
            <div className="text-center border-b border-slate-200 pb-4">
              <h2 className="text-2xl font-bold uppercase tracking-tight text-slate-900">
                {activeResume.sections?.contact?.full_name || 'Candidate Name'}
              </h2>
              {activeResume.sections?.contact?.headline && (
                <p className="text-xs font-bold text-brand-800 uppercase tracking-widest mt-1">
                  {activeResume.sections.contact.headline}
                </p>
              )}
              <p className="text-xs text-slate-500 mt-1.5 space-x-2">
                <span>{activeResume.sections?.contact?.email}</span>
                <span>•</span>
                <span>{activeResume.sections?.contact?.phone}</span>
                <span>•</span>
                <span>{activeResume.sections?.contact?.location}</span>
              </p>
            </div>

            {/* Summary */}
            {activeResume.sections?.summary && (
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-900 pb-1 mb-2">
                  Professional Summary
                </h4>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {activeResume.sections.summary}
                </p>
              </div>
            )}

            {/* Technical Skills */}
            {activeResume.sections?.skills?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-900 pb-1 mb-2">
                  Technical Skills
                </h4>
                <div className="flex flex-wrap gap-1.5 text-xs text-slate-800">
                  {activeResume.sections.skills.map((s: string, idx: number) => (
                    <span key={idx} className="bg-slate-100 px-2.5 py-0.5 rounded font-mono text-[11px]">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Experience */}
            {activeResume.sections?.experience?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-900 pb-1 mb-3">
                  Professional Experience
                </h4>
                <div className="space-y-4">
                  {activeResume.sections.experience.map((exp: any, idx: number) => (
                    <div key={idx} className="text-xs">
                      <div className="flex justify-between font-bold text-slate-900">
                        <span>{exp.job_title} — {exp.company}</span>
                        <span className="text-slate-500 font-normal">{exp.dates || exp.start_date}</span>
                      </div>
                      {exp.bullets?.length > 0 && (
                        <ul className="list-disc list-inside mt-1 space-y-1 text-slate-700">
                          {exp.bullets.map((b: string, bIdx: number) => (
                            <li key={bIdx}>{b}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Education */}
            {activeResume.sections?.education?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-900 pb-1 mb-2">
                  Education
                </h4>
                {activeResume.sections.education.map((edu: any, idx: number) => (
                  <div key={idx} className="flex justify-between text-xs text-slate-800">
                    <span><strong>{edu.degree}</strong> in {edu.field_of_study || 'General Studies'}, {edu.institution}</span>
                    <span className="text-slate-500">{edu.dates || edu.end_date}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Historical Versions Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Generated Resume History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {generatedList.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">No resumes generated yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase">
                  <tr>
                    <th className="p-4">Title / Role</th>
                    <th className="p-4">Target Company</th>
                    <th className="p-4">Version</th>
                    <th className="p-4">ATS Score</th>
                    <th className="p-4">Created</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {generatedList.map((res) => (
                    <tr key={res.id} className="hover:bg-slate-50">
                      <td className="p-4 font-semibold text-slate-900">{res.title}</td>
                      <td className="p-4 text-slate-600 text-xs">{res.target_company || '—'}</td>
                      <td className="p-4"><Badge variant="neutral">v{res.version_number}</Badge></td>
                      <td className="p-4">
                        {res.ats_score !== undefined && (
                          <Badge variant="brand">{res.ats_score.toFixed(0)}</Badge>
                        )}
                      </td>
                      <td className="p-4 text-slate-400 text-xs">{new Date(res.created_at).toLocaleDateString()}</td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => selectResumeToView(res.id)}
                          className="p-1 text-slate-400 hover:text-brand-600"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <a
                          href={api.generation.downloadUrl(res.id, 'pdf')}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1 inline-block text-slate-400 hover:text-brand-600"
                          title="Download PDF"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                        <button
                          onClick={() => handleDeleteGenerated(res.id)}
                          className="p-1 text-slate-400 hover:text-red-600"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Claim Provenance Modal */}
      <Modal
        isOpen={showProvenanceModal}
        onClose={() => setShowProvenanceModal(false)}
        title="Claim-Level Provenance & Zero-Hallucination Audit"
        description="Every claim in the tailored resume is strictly mapped back to verified source candidate evidence."
        maxWidth="2xl"
      >
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {activeResume?.claim_provenance?.length === 0 ? (
            <p className="text-xs text-slate-500">No provenance entries available.</p>
          ) : (
            activeResume?.claim_provenance?.map((claim: any, idx: number) => (
              <div key={idx} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 text-xs">
                <p className="font-semibold text-slate-900">"{claim.claim_text}"</p>
                <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-500">
                  <Badge variant="success" className="text-[10px]">Verified Fact</Badge>
                  <span>Source Document: <code className="font-mono">{claim.source_document_id || 'Uploaded CV'}</code></span>
                  {claim.confidence && <span>• Confidence: {(claim.confidence * 100).toFixed(0)}%</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </Modal>

      {/* Version Diff Modal */}
      <Modal
        isOpen={showVersionModal}
        onClose={() => setShowVersionModal(false)}
        title="Resume Version Comparison"
        description="Inspect differences and ATS score improvements across consecutive generations."
        maxWidth="xl"
      >
        {versionDiff && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
              <div>
                <p className="text-xs text-slate-500">Current Generation</p>
                <h4 className="text-lg font-bold text-slate-900">Version {versionDiff.current_version.version_number}</h4>
                <p className="text-xs text-brand-600 font-semibold">{versionDiff.current_version.ats_score?.toFixed(0)} ATS</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Previous Generation</p>
                <h4 className="text-lg font-bold text-slate-900">
                  {versionDiff.previous_version ? `Version ${versionDiff.previous_version.version_number}` : 'None'}
                </h4>
                <p className="text-xs text-slate-600">
                  {versionDiff.previous_version?.ats_score?.toFixed(0) || '—'} ATS
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-brand-100 bg-brand-50/30 text-xs text-slate-700 space-y-1">
              <p><strong>Version Delta:</strong> +{versionDiff.differences.version_difference} versions</p>
              <p>
                <strong>ATS Score Change:</strong>{' '}
                <span className={versionDiff.differences.ats_score_change >= 0 ? 'text-emerald-600 font-bold' : 'text-red-600'}>
                  {versionDiff.differences.ats_score_change >= 0 ? '+' : ''}{versionDiff.differences.ats_score_change} pts
                </span>
              </p>
              <p><strong>Is Latest Active:</strong> {versionDiff.differences.is_latest ? 'Yes' : 'No'}</p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
