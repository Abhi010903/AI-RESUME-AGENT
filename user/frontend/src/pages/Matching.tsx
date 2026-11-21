import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  GitCompare,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  ShieldAlert,
  Award,
  BookOpen,
  Briefcase,
  Layers,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'

export const Matching: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [profiles, setProfiles] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [selectedProfileId, setSelectedProfileId] = useState<string>('')
  const [selectedJobId, setSelectedJobId] = useState<string>('')

  const [matchResult, setMatchResult] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isMatching, setIsMatching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true)
        const [profs, jbs] = await Promise.all([api.profiles.list(), api.jobs.list()])
        setProfiles(profs)
        setJobs(jbs)

        const queryProf = searchParams.get('profile_id')
        const queryJob = searchParams.get('job_id')

        let pId = ''
        let jId = ''

        if (queryProf) pId = queryProf
        else if (profs.length > 0) pId = profs[0].id

        if (queryJob) jId = queryJob
        else if (jbs.length > 0) jId = jbs[0].id

        setSelectedProfileId(pId)
        setSelectedJobId(jId)

        // If match_id query param exists, load it
        const queryMatch = searchParams.get('match_id')
        if (queryMatch) {
          const m = await api.matches.get(queryMatch).catch(() => null)
          if (m) setMatchResult(m)
        }
      } catch (err: any) {
        setError(err.message || 'Failed to initialize matching')
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [searchParams])

  const handleRunMatch = async () => {
    if (!selectedProfileId || !selectedJobId) {
      setError('Please select both a candidate profile and a target job.')
      return
    }

    setIsMatching(true)
    setError(null)
    try {
      const result = await api.matches.create({
        profile_id: selectedProfileId,
        job_id: selectedJobId,
      })
      setMatchResult(result)
    } catch (err: any) {
      setError(err.message || 'Failed to compute match.')
    } finally {
      setIsMatching(false)
    }
  }

  const handleProceedToTailor = () => {
    if (!matchResult) return
    navigate(`/generation?profile_id=${selectedProfileId}&job_id=${selectedJobId}&match_id=${matchResult.id}`)
  }

  const selectedProfile = profiles.find((p) => p.id === selectedProfileId)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Evidence-Based Skill Matching Engine</h1>
        <p className="text-sm text-slate-500 mt-1">
          Evaluate how strictly and thoroughly your verified candidate profile satisfies all target job requirements.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {selectedProfile && !selectedProfile.is_approved && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-xl flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            <strong>Notice:</strong> This profile is in draft status. Matches can be evaluated for planning, but please review and formally approve your profile before finalizing tailored resumes.
          </span>
        </div>
      )}

      {/* Selection Form Card */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">Select Candidate Profile</label>
              {profiles.length === 0 ? (
                <p className="text-xs text-slate-400">No profile found. Please consolidate resumes first.</p>
              ) : (
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-sm bg-white focus:ring-2 focus:ring-brand-500"
                >
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} ({p.headline || 'Profile'}) {p.is_approved ? '✓ Approved' : '(Draft)'}
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
              onClick={handleRunMatch}
              isLoading={isMatching}
              disabled={!selectedProfileId || !selectedJobId}
              className="shadow-md"
            >
              <GitCompare className="w-4 h-4" /> Compute Evidence Match
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Match Results Display */}
      {matchResult && (
        <div className="space-y-6">
          {/* Stale Invalidation Banner */}
          {matchResult.is_stale && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <div>
                  <span className="font-bold">Stale Match Assessment: </span>
                  <span>{matchResult.stale_reason || 'The candidate profile or job description was updated since this match was computed.'}</span>
                </div>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={handleRunMatch}
                isLoading={isMatching}
                className="bg-amber-600 hover:bg-amber-700 text-white font-semibold flex-shrink-0"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1" /> Recompute Match
              </Button>
            </div>
          )}

          {/* Top Score Summary Banner */}
          <Card className="bg-gradient-to-br from-slate-900 to-brand-950 text-white border-0 shadow-xl overflow-hidden">
            <CardContent className="p-8 flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="flex items-center gap-6">
                <div className="w-28 h-28 rounded-full border-4 border-brand-400/40 bg-brand-500/10 flex flex-col items-center justify-center text-center">
                  <span className="text-4xl font-extrabold tracking-tight text-brand-300">
                    {matchResult.overall_score.toFixed(0)}%
                  </span>
                  <span className="text-[10px] text-slate-300 uppercase tracking-widest font-semibold mt-0.5">Overall Fit</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-white">Match Assessment Completed</h3>
                    {matchResult.is_stale && (
                      <Badge variant="warning" className="text-xs">Stale</Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-300 mt-1 max-w-md">
                    Based on verified candidate experiences, skills, education, and domain certifications against extracted role requirements.
                  </p>
                  <div className="flex items-center gap-3 mt-3">
                    <Badge variant="brand" className="bg-brand-500/20 text-brand-200 border-brand-400/30">
                      Evidence Coverage: {(matchResult.evidence_coverage * 100).toFixed(0)}%
                    </Badge>
                    {matchResult.conflict_impact > 0 && (
                      <Badge variant="warning" className="bg-amber-500/20 text-amber-200 border-amber-400/30">
                        Conflict Impact: -{(matchResult.conflict_impact * 100).toFixed(0)}%
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              <Button
                variant="primary"
                onClick={handleProceedToTailor}
                className="bg-brand-500 hover:bg-brand-400 text-white font-semibold shadow-lg py-3 px-6 text-sm flex-shrink-0"
              >
                <Sparkles className="w-4 h-4" /> Tailor Resume with this Match <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </CardContent>
          </Card>

          {/* 6 Dimensions Breakdown Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'Mandatory Skills', score: matchResult.mandatory_skill_score, icon: CheckCircle2 },
              { label: 'Preferred Skills', score: matchResult.preferred_skill_score, icon: Award },
              { label: 'Experience Align.', score: matchResult.experience_score, icon: Briefcase },
              { label: 'Education Align.', score: matchResult.education_score, icon: BookOpen },
              { label: 'Domain Fit', score: matchResult.domain_score, icon: Layers },
              { label: 'Certifications', score: matchResult.certification_score, icon: Award },
            ].map((dim, idx) => {
              const Icon = dim.icon
              return (
                <Card key={idx} className="text-center p-4">
                  <Icon className="w-5 h-5 text-brand-600 mx-auto mb-2" />
                  <p className="text-xs text-slate-500 font-medium truncate">{dim.label}</p>
                  <p className="text-xl font-bold text-slate-900 mt-1">{dim.score?.toFixed(0) || 0}%</p>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-brand-600 h-full rounded-full"
                      style={{ width: `${dim.score || 0}%` }}
                    />
                  </div>
                </Card>
              )
            })}
          </div>

          {/* Two Columns: Requirement Matches & Gap Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Matched Requirements Checklist */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Requirement Matches & Evidence</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 max-h-96 overflow-y-auto">
                {matchResult.requirement_matches?.length === 0 ? (
                  <p className="text-xs text-slate-500">No matched requirements recorded.</p>
                ) : (
                  matchResult.requirement_matches?.map((rm: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 flex items-start gap-3"
                    >
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-semibold text-slate-900 truncate">{rm.requirement_name}</p>
                          <Badge variant="brand" className="text-[10px]">
                            {rm.match_status}
                          </Badge>
                        </div>
                        {rm.evidence_excerpt && (
                          <p className="text-xs text-slate-600 mt-1 italic">
                            "{rm.evidence_excerpt}"
                          </p>
                        )}
                        <p className="text-[11px] text-slate-400 mt-1">
                          Category: {rm.category} • Confidence: {(rm.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Gap Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Skill & Experience Gap Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 max-h-96 overflow-y-auto">
                {matchResult.gaps?.length === 0 ? (
                  <div className="p-6 text-center text-emerald-600 text-sm font-medium">
                    ✓ Outstanding! No critical skill or qualification gaps identified.
                  </div>
                ) : (
                  matchResult.gaps?.map((gap: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-amber-200 bg-amber-50/40 flex items-start gap-3"
                    >
                      <XCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-slate-900">{gap.requirement_name || gap.skill_name || 'Missing Requirement'}</p>
                        <p className="text-xs text-slate-700 mt-1">
                          {gap.recommendation || 'Consider highlighting related projects or completing coursework.'}
                        </p>
                        <span className="text-[10px] text-slate-500 font-medium uppercase mt-1 block">
                          Type: {gap.gap_type || gap.category || 'Skill Gap'}
                        </span>
                      </div>
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
