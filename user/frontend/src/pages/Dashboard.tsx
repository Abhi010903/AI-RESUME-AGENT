import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FileText,
  Briefcase,
  Wand2,
  Kanban,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Download,
  Sparkles,
  GitCompare,
  Activity,
  Layers,
  ShieldCheck,
  Check,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'

export const Dashboard: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [workflow, setWorkflow] = useState<any | null>(null)
  const [activities, setActivities] = useState<any[]>([])
  const [recentGenerated, setRecentGenerated] = useState<any[]>([])
  const [recentApplications, setRecentApplications] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadDashboard() {
      try {
        setIsLoading(true)
        const [wfStatus, actFeed, genList, appList] = await Promise.all([
          api.workflow.status().catch(() => null),
          api.workflow.activity(8).catch(() => []),
          api.generation.list(5).catch(() => []),
          api.applications.list().catch(() => []),
        ])

        setWorkflow(wfStatus)
        setActivities(actFeed)
        setRecentGenerated(genList)
        setRecentApplications(appList.slice(0, 5))
      } catch (err) {
        console.error('Failed to load dashboard:', err)
      } finally {
        setIsLoading(false)
      }
    }
    loadDashboard()
  }, [])

  const metrics = workflow?.metrics || {
    resumes_count: 0,
    profile_status: 'not_consolidated',
    profile_completeness: 0,
    verified_skills_count: 0,
    projects_count: 0,
    experience_count: 0,
    certifications_count: 0,
    jobs_count: 0,
    matches_count: 0,
    generated_resumes_count: 0,
    ats_evaluations_count: 0,
    applications_count: 0,
  }

  const primaryAction = workflow?.primary_action
  const stages = workflow?.stages || []

  return (
    <div className="space-y-8">
      {/* 1. Welcome & Primary Recommended Action Header */}
      <div className="bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 rounded-2xl p-8 text-white shadow-xl border border-slate-800 relative overflow-hidden">
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs uppercase tracking-wider font-semibold text-brand-400 bg-brand-950/80 px-2.5 py-1 rounded border border-brand-800/50">
                Authoritative Candidate Workspace
              </span>
              <Badge
                variant={metrics.profile_status === 'approved' ? 'success' : 'neutral'}
                className="text-xs"
              >
                {metrics.profile_status === 'approved' ? '✓ Profile Approved' : 'Draft / Needs Review'}
              </Badge>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Welcome back, {user?.full_name || 'Candidate'}
            </h1>
            {workflow?.headline && (
              <p className="text-sm font-medium text-brand-300 mt-1">
                {workflow.headline}
              </p>
            )}
            <p className="mt-2 text-slate-300 text-sm leading-relaxed">
              Maintain your career knowledge base, verify evidence-backed claims, compute target role compatibility, and generate ATS-guaranteed single-page resumes.
            </p>
          </div>

          {/* Dynamic Next Action Card */}
          {primaryAction && (
            <div className="bg-white/10 backdrop-blur-md border border-white/15 rounded-xl p-5 lg:w-96 flex flex-col justify-between shadow-lg">
              <div>
                <div className="flex items-center justify-between text-xs font-semibold text-brand-300 uppercase tracking-wider">
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" /> Recommended Next Action
                  </span>
                  <span className="text-[10px] bg-brand-500/20 px-1.5 py-0.5 rounded text-white border border-brand-400/30">
                    {primaryAction.priority} priority
                  </span>
                </div>
                <h3 className="text-base font-bold text-white mt-1.5">{primaryAction.title}</h3>
                <p className="text-xs text-slate-300 mt-1 leading-normal">{primaryAction.description}</p>
                <p className="text-[11px] text-slate-400 mt-2 italic">Why: {primaryAction.reason}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/10 flex justify-end">
                <Link to={primaryAction.action_url}>
                  <Button variant="primary" size="sm" className="bg-brand-500 hover:bg-brand-400 text-white font-semibold shadow-md">
                    {primaryAction.action_label} <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2. Live KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Link to="/resumes" className="block group">
          <Card className="hover:border-brand-300 transition-all group-hover:shadow-md">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Source Resumes</p>
                <h4 className="text-2xl font-bold text-slate-900 mt-0.5">{metrics.resumes_count}</h4>
                <span className="text-xs text-brand-600 font-medium flex items-center gap-1 mt-0.5">
                  Manage files <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/profile" className="block group">
          <Card className="hover:border-brand-300 transition-all group-hover:shadow-md">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Profile Completeness</p>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <h4 className="text-2xl font-bold text-slate-900">{metrics.profile_completeness}%</h4>
                  <span className="text-xs text-slate-500">({metrics.verified_skills_count} verified skills)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2">
                  <div
                    className="bg-emerald-500 h-1.5 rounded-full transition-all"
                    style={{ width: `${metrics.profile_completeness}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/jobs" className="block group">
          <Card className="hover:border-brand-300 transition-all group-hover:shadow-md">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                <Briefcase className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Target Jobs</p>
                <h4 className="text-2xl font-bold text-slate-900 mt-0.5">{metrics.jobs_count}</h4>
                <span className="text-xs text-brand-600 font-medium flex items-center gap-1 mt-0.5">
                  {metrics.matches_count} computed matches <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/applications" className="block group">
          <Card className="hover:border-brand-300 transition-all group-hover:shadow-md">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                <Kanban className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Applications</p>
                <h4 className="text-2xl font-bold text-slate-900 mt-0.5">{metrics.applications_count}</h4>
                <span className="text-xs text-brand-600 font-medium flex items-center gap-1 mt-0.5">
                  Pipeline tracker <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* 3. 12-Stage Interactive Candidate Lifecycle Progress Tracker */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100">
          <div>
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand-600" /> Complete 12-Stage Candidate Lifecycle Tracker
            </CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Real-time progress orchestration from resume upload to final application offer.
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded">
            {stages.filter((s: any) => s.status === 'completed').length} / 12 Stages Completed
          </span>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {stages.map((stage: any, idx: number) => {
              const isDone = stage.status === 'completed'
              const isBlocked = stage.status === 'blocked'
              const isNeedsAttn = stage.status === 'needs_attention'
              const isInProgress = stage.status === 'in_progress'

              return (
                <div
                  key={stage.key}
                  className={`p-4 rounded-xl border transition-all flex flex-col justify-between ${
                    isDone
                      ? 'bg-emerald-50/40 border-emerald-200'
                      : isNeedsAttn
                      ? 'bg-amber-50/50 border-amber-300'
                      : isInProgress
                      ? 'bg-blue-50/50 border-blue-200'
                      : isBlocked
                      ? 'bg-slate-50 border-slate-200 opacity-70'
                      : 'bg-white border-slate-200'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-[11px] font-bold text-slate-400 font-mono">
                        Step {idx + 1}
                      </span>
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                          isDone
                            ? 'bg-emerald-100 text-emerald-800'
                            : isNeedsAttn
                            ? 'bg-amber-100 text-amber-800'
                            : isInProgress
                            ? 'bg-blue-100 text-blue-800'
                            : isBlocked
                            ? 'bg-slate-200 text-slate-600'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {stage.status.replace('_', ' ')}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900">{stage.label}</h4>
                    <p className="text-xs text-slate-600 mt-1 leading-normal">{stage.description}</p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-center justify-between">
                    {isBlocked ? (
                      <span className="text-[11px] text-slate-400 font-medium">Prerequisites pending</span>
                    ) : (
                      <Link to={stage.action_url} className="w-full">
                        <Button
                          variant={isDone ? 'outline' : 'primary'}
                          size="sm"
                          className="w-full text-xs font-semibold py-1.5"
                        >
                          {stage.action_label} <ArrowRight className="w-3 h-3 ml-1" />
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* 4. Three Column Activity & Snapshot Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Real Activity Stream */}
        <Card className="lg:col-span-1">
          <CardHeader className="border-b border-slate-100">
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-600" /> Recent Audit Activity
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {activities.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">No recent actions recorded.</div>
            ) : (
              <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                {activities.map((act) => (
                  <div key={act.id} className="p-3.5 hover:bg-slate-50 transition-colors text-xs">
                    <p className="font-semibold text-slate-800">{act.title}</p>
                    {act.description && <p className="text-slate-500 text-[11px] mt-0.5">{act.description}</p>}
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} •{' '}
                      {new Date(act.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Generated Resumes */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex items-center justify-between border-b border-slate-100">
            <CardTitle className="text-base font-bold text-slate-900">Tailored Resumes</CardTitle>
            <Link to="/generation" className="text-xs text-brand-600 font-medium hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {recentGenerated.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No resumes generated yet.
                <div className="mt-3">
                  <Link to="/generation">
                    <Button variant="outline" size="sm">
                      <Wand2 className="w-3.5 h-3.5 mr-1" /> Tailor Resume
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                {recentGenerated.map((res) => (
                  <div key={res.id} className="p-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors">
                    <div>
                      <p className="text-xs font-bold text-slate-900">{res.title}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {res.target_role} • v{res.version_number}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {res.ats_score !== undefined && (
                        <Badge variant="brand" className="text-[10px] px-1.5 py-0.5">
                          {res.ats_score.toFixed(0)} ATS
                        </Badge>
                      )}
                      <a
                        href={api.generation.downloadUrl(res.id, 'pdf')}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1 text-slate-500 hover:text-brand-600 rounded"
                        title="Download PDF"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Application Pipeline Snapshot */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex items-center justify-between border-b border-slate-100">
            <CardTitle className="text-base font-bold text-slate-900">Active Applications</CardTitle>
            <Link to="/applications" className="text-xs text-brand-600 font-medium hover:underline flex items-center gap-1">
              Open Board <ArrowRight className="w-3 h-3" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {recentApplications.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No applications tracked yet.
                <div className="mt-3">
                  <Link to="/applications">
                    <Button variant="outline" size="sm">
                      <Kanban className="w-3.5 h-3.5 mr-1" /> Track Application
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                {recentApplications.map((app) => (
                  <div key={app.id} className="p-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors">
                    <div>
                      <p className="text-xs font-bold text-slate-900">{app.position_title}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">{app.company}</p>
                    </div>
                    <Badge variant="neutral" className="text-[10px] px-2 py-0.5 font-semibold">
                      {app.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
