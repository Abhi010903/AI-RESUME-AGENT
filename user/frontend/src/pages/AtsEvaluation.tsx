import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sparkles,
  BarChart3,
  FileCheck,
  ShieldAlert,
  ListChecks,
  TrendingUp,
  Wand2,
  ArrowRight,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'

export const AtsEvaluation: React.FC = () => {
  const navigate = useNavigate()
  const [resumes, setResumes] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])

  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [selectedJobId, setSelectedJobId] = useState('')

  const [evaluation, setEvaluation] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true)
        const [genResumes, jbs] = await Promise.all([
          api.generation.list(),
          api.jobs.list(),
        ])
        setResumes(genResumes)
        setJobs(jbs)

        if (genResumes.length > 0) setSelectedResumeId(genResumes[0].id)
        if (jbs.length > 0) setSelectedJobId(jbs[0].id)

        // If resumes exist, check for past reports
        if (genResumes.length > 0) {
          const reports = await api.ats.list(genResumes[0].id).catch(() => [])
          if (reports && reports.length > 0) {
            setEvaluation(reports[0])
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to initialize ATS evaluation')
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  const handleRunEvaluation = async () => {
    if (!selectedResumeId || !selectedJobId) {
      setError('Please select both a tailored resume and a target job.')
      return
    }

    setIsEvaluating(true)
    setError(null)
    try {
      const result = await api.ats.evaluate({
        resume_id: selectedResumeId,
        job_id: selectedJobId,
      })
      setEvaluation(result)
    } catch (err: any) {
      setError(err.message || 'Evaluation failed.')
    } finally {
      setIsEvaluating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Transparent 7-Dimension ATS Evaluation</h1>
        <p className="text-sm text-slate-500 mt-1">
          Simulate enterprise applicant tracking parsing (Workday, Greenhouse, Taleo) across 7 transparent dimensions with keyword stuffing checks.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Select Resume & Job */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">Select Tailored Resume</label>
              {resumes.length === 0 ? (
                <p className="text-xs text-slate-400">No tailored resumes found. Please generate one first.</p>
              ) : (
                <select
                  value={selectedResumeId}
                  onChange={(e) => setSelectedResumeId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-sm bg-white focus:ring-2 focus:ring-brand-500"
                >
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.title} (v{r.version_number})
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">Select Target Job Description</label>
              {jobs.length === 0 ? (
                <p className="text-xs text-slate-400">No jobs found. Please add a target job first.</p>
              ) : (
                <select
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-sm bg-white focus:ring-2 focus:ring-brand-500"
                >
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title} at {j.company || 'Unknown Company'}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <Button
              variant="primary"
              onClick={handleRunEvaluation}
              isLoading={isEvaluating}
              disabled={!selectedResumeId || !selectedJobId}
              className="shadow-md"
            >
              <FileCheck className="w-4 h-4" /> Run ATS Audit
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Evaluation Results */}
      {evaluation && (
        <div className="space-y-6">
          {/* Main Score Hero Card */}
          <Card className="bg-gradient-to-br from-slate-900 to-slate-950 text-white border-0 shadow-xl overflow-hidden">
            <CardContent className="p-8 flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="flex items-center gap-6">
                <div
                  className={`w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center text-center ${
                    evaluation.overall_score >= 80
                      ? 'border-emerald-400/50 bg-emerald-500/10 text-emerald-400'
                      : evaluation.overall_score >= 60
                      ? 'border-amber-400/50 bg-amber-500/10 text-amber-400'
                      : 'border-red-400/50 bg-red-500/10 text-red-400'
                  }`}
                >
                  <span className="text-4xl font-extrabold tracking-tight">
                    {evaluation.overall_score?.toFixed(0)}
                  </span>
                  <span className="text-[10px] uppercase tracking-widest font-semibold mt-0.5">ATS Score</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-white">
                      {evaluation.overall_score >= 80
                        ? 'High Interview Probability'
                        : evaluation.overall_score >= 60
                        ? 'Moderate Candidate Alignment'
                        : 'ATS Optimization Needed'}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-300 mt-1 max-w-md">
                    Evaluated across 7 transparent ATS criteria: mandatory skills, preferred skills, experience alignment, education alignment, keyword density, structure parsability, and readability.
                  </p>
                  {evaluation.report?.keyword_stuffing_warning && (
                    <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-amber-500/20 text-amber-300 text-xs border border-amber-500/30">
                      <AlertTriangle className="w-3.5 h-3.5" /> Keyword Stuffing Detected
                    </div>
                  )}
                </div>
              </div>

              <Button
                variant="primary"
                onClick={() => {
                  navigate(`/generation?job_id=${selectedJobId}&resume_id=${selectedResumeId}&from_ats=true`)
                }}
                className="bg-brand-500 hover:bg-brand-400 text-white font-semibold py-3 px-6 shadow-md flex-shrink-0"
              >
                <Wand2 className="w-4 h-4 mr-1.5" /> Improve Resume in Builder <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </CardContent>
          </Card>

          {/* 7 Dimensions Transparent Gauges */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {[
              { label: 'Mandatory Skills', score: evaluation.mandatory_skill_score },
              { label: 'Preferred Skills', score: evaluation.preferred_skill_score },
              { label: 'Experience Align.', score: evaluation.experience_score },
              { label: 'Education Align.', score: evaluation.education_score },
              { label: 'Keyword Relevance', score: evaluation.keyword_score },
              { label: 'Structure / Format', score: evaluation.structure_score },
              { label: 'Readability Score', score: evaluation.readability_score },
            ].map((dim, idx) => (
              <Card key={idx} className="p-4 text-center">
                <p className="text-xs text-slate-500 font-medium truncate">{dim.label}</p>
                <p className="text-xl font-bold text-slate-900 mt-1">{dim.score?.toFixed(0) || 0}%</p>
                <div className="w-full bg-slate-100 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      (dim.score || 0) >= 80 ? 'bg-emerald-500' : (dim.score || 0) >= 60 ? 'bg-brand-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${dim.score || 0}%` }}
                  />
                </div>
              </Card>
            ))}
          </div>

          {/* Keyword Coverage & Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Keywords Coverage */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Mandatory Skill & Keyword Coverage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Matched In Resume</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {evaluation.report?.matched_mandatory_skills?.length === 0 ? (
                      <span className="text-xs text-slate-400">None matched</span>
                    ) : (
                      evaluation.report?.matched_mandatory_skills?.map((sk: string, idx: number) => (
                        <Badge key={idx} variant="success" className="text-xs">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> {sk}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Missing Mandatory Skills</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {evaluation.report?.missing_mandatory_skills?.length === 0 ? (
                      <span className="text-xs text-emerald-600 font-medium">All mandatory skills matched!</span>
                    ) : (
                      evaluation.report?.missing_mandatory_skills?.map((sk: string, idx: number) => (
                        <Badge key={idx} variant="error" className="text-xs">
                          <XCircle className="w-3 h-3 text-red-500" /> {sk}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Actionable Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Actionable ATS Recommendations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {evaluation.report?.actionable_recommendations?.length === 0 ? (
                  <p className="text-xs text-slate-500">No recommendations. Resume demonstrates strong ATS alignment.</p>
                ) : (
                  evaluation.report?.actionable_recommendations?.map((rec: string, idx: number) => (
                    <div key={idx} className="p-3 rounded-lg border border-brand-100 bg-brand-50/40 text-xs text-slate-800 flex items-start gap-2.5">
                      <Sparkles className="w-4 h-4 text-brand-600 flex-shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
