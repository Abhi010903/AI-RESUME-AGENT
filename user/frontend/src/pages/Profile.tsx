import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  User as UserIcon,
  Briefcase,
  GraduationCap,
  Award,
  Code,
  FolderGit2,
  AlertTriangle,
  CheckCircle2,
  Plus,
  Trash2,
  Edit2,
  ShieldCheck,
  ExternalLink,
  Save,
  Check,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'

export const Profile: React.FC = () => {
  const [profile, setProfile] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<
    'experience' | 'education' | 'skills' | 'certifications' | 'projects' | 'conflicts'
  >('experience')

  // Modals
  const [showAddExp, setShowAddExp] = useState(false)
  const [showAddEdu, setShowAddEdu] = useState(false)
  const [showAddSkill, setShowAddSkill] = useState(false)
  const [showAddCert, setShowAddCert] = useState(false)
  const [showAddProject, setShowAddProject] = useState(false)
  const [showEditContact, setShowEditContact] = useState(false)

  // Form states
  const [expForm, setExpForm] = useState({
    company: '',
    job_title: '',
    location: '',
    start_date: '',
    end_date: '',
    is_current: false,
    description: '',
    skills_used: '',
  })
  const [eduForm, setEduForm] = useState({
    institution: '',
    degree: '',
    field_of_study: '',
    start_date: '',
    end_date: '',
    grade: '',
  })
  const [skillForm, setSkillForm] = useState({
    name: '',
    category: 'Backend',
    proficiency: 'intermediate',
    years_of_experience: 1,
  })
  const [certForm, setCertForm] = useState({
    name: '',
    issuing_organization: '',
    issue_date: '',
    expiry_date: '',
    credential_id: '',
    credential_url: '',
  })
  const [projectForm, setProjectForm] = useState({
    name: '',
    subtitle: '',
    technologies: '',
    bullets: '',
  })
  const [contactForm, setContactForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    headline: '',
    summary: '',
    linkedin_url: '',
    github_url: '',
  })

  // Conflict resolution
  const [resolvingConflictId, setResolvingConflictId] = useState<string | null>(null)
  const [resolutionStatus, setResolutionStatus] = useState<'resolved' | 'dismissed'>('resolved')
  const [resolutionNotes, setResolutionNotes] = useState('')

  const loadProfile = async () => {
    try {
      setIsLoading(true)
      const profiles = await api.profiles.list()
      if (profiles && profiles.length > 0) {
        const fullProf = await api.profiles.get(profiles[0].id)
        setProfile(fullProf)
        setContactForm({
          full_name: fullProf.full_name || '',
          email: fullProf.email || '',
          phone: fullProf.phone || '',
          location: fullProf.location || '',
          headline: fullProf.headline || '',
          summary: fullProf.summary || '',
          linkedin_url: fullProf.linkedin_url || '',
          github_url: fullProf.github_url || '',
        })
      } else {
        setProfile(null)
      }
    } catch (err) {
      console.error('Failed to load profile:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadProfile()
  }, [])

  const handleApproveAll = async () => {
    if (!profile) return
    try {
      const updated = await api.profiles.approve(profile.id, { approve_all: true })
      setProfile(updated)
    } catch (err: any) {
      alert(err.message || 'Approval failed.')
    }
  }

  const handleSaveContact = async () => {
    if (!profile) return
    try {
      const updated = await api.profiles.update(profile.id, contactForm)
      setProfile(updated)
      setShowEditContact(false)
    } catch (err: any) {
      alert(err.message || 'Failed to update contact.')
    }
  }

  const handleCreateExperience = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profile) return
    try {
      await api.profiles.addExperience(profile.id, {
        ...expForm,
        skills_used: expForm.skills_used ? expForm.skills_used.split(',').map((s) => s.trim()) : [],
      })
      await loadProfile()
      setShowAddExp(false)
      setExpForm({
        company: '',
        job_title: '',
        location: '',
        start_date: '',
        end_date: '',
        is_current: false,
        description: '',
        skills_used: '',
      })
    } catch (err: any) {
      alert(err.message || 'Failed to add experience.')
    }
  }

  const handleDeleteExperience = async (expId: string) => {
    if (!profile || !window.confirm('Delete this experience?')) return
    await api.profiles.deleteExperience(profile.id, expId)
    await loadProfile()
  }

  const handleCreateEducation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profile) return
    try {
      await api.profiles.addEducation(profile.id, eduForm)
      await loadProfile()
      setShowAddEdu(false)
      setEduForm({ institution: '', degree: '', field_of_study: '', start_date: '', end_date: '', grade: '' })
    } catch (err: any) {
      alert(err.message || 'Failed to add education.')
    }
  }

  const handleDeleteEducation = async (eduId: string) => {
    if (!profile || !window.confirm('Delete this education record?')) return
    await api.profiles.deleteEducation(profile.id, eduId)
    await loadProfile()
  }

  const handleCreateSkill = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profile) return
    try {
      await api.profiles.addSkill(profile.id, {
        ...skillForm,
        years_of_experience: Number(skillForm.years_of_experience) || 1,
      })
      await loadProfile()
      setShowAddSkill(false)
      setSkillForm({ name: '', category: 'Backend', proficiency: 'intermediate', years_of_experience: 1 })
    } catch (err: any) {
      alert(err.message || 'Failed to add skill.')
    }
  }

  const handleDeleteSkill = async (skillId: string) => {
    if (!profile || !window.confirm('Delete this skill?')) return
    await api.profiles.deleteSkill(profile.id, skillId)
    await loadProfile()
  }

  const handleCreateCert = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profile) return
    try {
      await api.profiles.addCertification(profile.id, certForm)
      await loadProfile()
      setShowAddCert(false)
      setCertForm({ name: '', issuing_organization: '', issue_date: '', expiry_date: '', credential_id: '', credential_url: '' })
    } catch (err: any) {
      alert(err.message || 'Failed to add certification.')
    }
  }

  const handleDeleteCert = async (certId: string) => {
    if (!profile || !window.confirm('Delete this certification?')) return
    await api.profiles.deleteCertification(profile.id, certId)
    await loadProfile()
  }

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profile) return
    try {
      await api.profiles.addProject(profile.id, {
        name: projectForm.name,
        subtitle: projectForm.subtitle || undefined,
        technologies: projectForm.technologies ? projectForm.technologies.split(',').map((t) => t.trim()) : [],
        bullets: projectForm.bullets ? projectForm.bullets.split('\n').filter(Boolean) : [],
      })
      await loadProfile()
      setShowAddProject(false)
      setProjectForm({ name: '', subtitle: '', technologies: '', bullets: '' })
    } catch (err: any) {
      alert(err.message || 'Failed to add project.')
    }
  }

  const handleDeleteProject = async (index: number) => {
    if (!profile || !window.confirm('Delete this project?')) return
    await api.profiles.deleteProject(profile.id, index)
    await loadProfile()
  }

  const handleResolveConflict = async () => {
    if (!profile || !resolvingConflictId) return
    try {
      const updated = await api.profiles.resolveConflict(profile.id, resolvingConflictId, {
        resolution_status: resolutionStatus,
        resolution_notes: resolutionNotes || 'Resolved by candidate',
      })
      setProfile(updated)
      setResolvingConflictId(null)
      setResolutionNotes('')
    } catch (err: any) {
      alert(err.message || 'Failed to resolve conflict.')
    }
  }

  if (isLoading) {
    return <div className="p-12 text-center text-slate-500 text-sm">Loading verified candidate profile...</div>
  }

  if (!profile) {
    return (
      <Card className="text-center p-12">
        <UserIcon className="w-12 h-12 text-slate-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-900">No Consolidated Profile Found</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto mt-2">
          Upload your existing resumes in the Resumes workspace and consolidate them to generate your profile.
        </p>
        <div className="mt-6">
          <Link to="/resumes">
            <Button variant="primary">Go to Resumes & Upload</Button>
          </Link>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Profile Overview Card */}
      <Card className="border-brand-100 shadow-sm">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-500 text-white flex items-center justify-center text-2xl font-bold uppercase shadow-md flex-shrink-0">
                {profile.full_name ? profile.full_name[0] : 'U'}
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold text-slate-900">{profile.full_name}</h1>
                  <Badge
                    variant={
                      profile.verification_status === 'approved'
                        ? 'success'
                        : profile.verification_status === 'partially_verified'
                        ? 'warning'
                        : 'brand'
                    }
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    {profile.verification_status}
                  </Badge>
                </div>
                <p className="text-sm font-medium text-brand-700 mt-0.5">{profile.headline || 'No headline set'}</p>
                <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500 mt-2">
                  {profile.email && <span>{profile.email}</span>}
                  {profile.phone && <span>{profile.phone}</span>}
                  {profile.location && <span>{profile.location}</span>}
                  {profile.linkedin_url && (
                    <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline inline-flex items-center gap-0.5">
                      LinkedIn <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  )}
                  {profile.github_url && (
                    <a href={profile.github_url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline inline-flex items-center gap-0.5">
                      GitHub <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={() => setShowEditContact(true)}>
                <Edit2 className="w-3.5 h-3.5" /> Edit Details
              </Button>
              {!profile.is_approved && (
                <Button variant="primary" size="sm" onClick={handleApproveAll}>
                  <Check className="w-3.5 h-3.5" /> Approve Profile
                </Button>
              )}
            </div>
          </div>

          {profile.summary && (
            <p className="mt-4 pt-4 border-t border-slate-100 text-xs text-slate-600 leading-relaxed">
              {profile.summary}
            </p>
          )}

          {/* Completeness Bar */}
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between gap-4 text-xs">
            <span className="text-slate-500">Profile Completeness: <strong className="text-slate-800">{profile.completeness_percentage}%</strong></span>
            <div className="flex-1 max-w-xs bg-slate-100 h-2 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full transition-all" style={{ width: `${profile.completeness_percentage}%` }} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto text-sm">
        {[
          { key: 'experience', label: 'Work Experience', icon: Briefcase, count: profile.experiences?.length },
          { key: 'education', label: 'Education', icon: GraduationCap, count: profile.education?.length },
          { key: 'skills', label: 'Technical Skills', icon: Code, count: profile.skills?.length },
          { key: 'certifications', label: 'Certifications', icon: Award, count: profile.certifications?.length },
          { key: 'projects', label: 'Projects', icon: FolderGit2, count: profile.projects?.length },
          { key: 'conflicts', label: 'Conflicts & Audit', icon: AlertTriangle, count: profile.conflicts?.length },
        ].map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                isActive
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    isActive ? 'bg-slate-800 text-slate-200' : 'bg-slate-200/80 text-slate-700'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab 1: Work Experience */}
      {activeTab === 'experience' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold">Employment History</CardTitle>
            <Button size="sm" onClick={() => setShowAddExp(true)}>
              <Plus className="w-3.5 h-3.5" /> Add Experience
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile.experiences?.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">No work experience entries recorded.</p>
            ) : (
              profile.experiences.map((exp: any) => (
                <div key={exp.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{exp.job_title}</h4>
                      <p className="text-xs text-brand-700 font-medium">{exp.company} {exp.location ? `• ${exp.location}` : ''}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {exp.start_date} – {exp.is_current ? 'Present' : exp.end_date || 'N/A'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {exp.is_approved ? (
                        <Badge variant="success">Approved</Badge>
                      ) : (
                        <Badge variant="warning">Unapproved</Badge>
                      )}
                      <button
                        onClick={() => handleDeleteExperience(exp.id)}
                        className="p-1 text-slate-400 hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  {exp.description && (
                    <p className="mt-2 text-xs text-slate-600 whitespace-pre-line leading-relaxed">{exp.description}</p>
                  )}
                  {exp.skills_used?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {exp.skills_used.map((sk: string) => (
                        <Badge key={sk} variant="neutral" className="text-[10px]">
                          {sk}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 2: Education */}
      {activeTab === 'education' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold">Academic Qualifications</CardTitle>
            <Button size="sm" onClick={() => setShowAddEdu(true)}>
              <Plus className="w-3.5 h-3.5" /> Add Education
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile.education?.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">No academic degrees recorded.</p>
            ) : (
              profile.education.map((edu: any) => (
                <div key={edu.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{edu.degree} in {edu.field_of_study || 'General Studies'}</h4>
                    <p className="text-xs text-brand-700 font-medium">{edu.institution}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {edu.start_date} – {edu.end_date || 'Present'} {edu.grade ? `• Grade: ${edu.grade}` : ''}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDeleteEducation(edu.id)}
                    className="p-1 text-slate-400 hover:text-red-600 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Skills */}
      {activeTab === 'skills' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold">Verified Technical Skills</CardTitle>
            <Button size="sm" onClick={() => setShowAddSkill(true)}>
              <Plus className="w-3.5 h-3.5" /> Add Skill
            </Button>
          </CardHeader>
          <CardContent>
            {profile.skills?.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">No skills recorded.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {profile.skills.map((sk: any) => (
                  <div key={sk.id} className="p-3 rounded-xl border border-slate-200 bg-white shadow-xs flex items-center justify-between hover:border-brand-200 transition-all">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{sk.name}</p>
                      <p className="text-[11px] text-slate-400">{sk.category} • {sk.years_of_experience} yrs</p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Badge variant="brand" className="text-[10px] uppercase font-mono">{sk.proficiency || 'med'}</Badge>
                      <button
                        onClick={() => handleDeleteSkill(sk.id)}
                        className="p-1 text-slate-400 hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 4: Certifications */}
      {activeTab === 'certifications' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold">Licenses & Certifications</CardTitle>
            <Button size="sm" onClick={() => setShowAddCert(true)}>
              <Plus className="w-3.5 h-3.5" /> Add Certification
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile.certifications?.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">No certifications recorded.</p>
            ) : (
              profile.certifications.map((c: any) => (
                <div key={c.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{c.name}</h4>
                    <p className="text-xs text-brand-700 font-medium">{c.issuing_organization}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">Issued: {c.issue_date || 'N/A'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {c.credential_url && (
                      <a href={c.credential_url} target="_blank" rel="noreferrer" className="text-xs text-brand-600 hover:underline inline-flex items-center gap-1">
                        Verify <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    <button
                      onClick={() => handleDeleteCert(c.id)}
                      className="p-1 text-slate-400 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 5: Projects */}
      {activeTab === 'projects' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold">Key Projects</CardTitle>
            <Button size="sm" onClick={() => setShowAddProject(true)}>
              <Plus className="w-3.5 h-3.5" /> Add Project
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile.projects?.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">No portfolio projects recorded.</p>
            ) : (
              profile.projects.map((proj: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{proj.name}</h4>
                      {proj.subtitle && <p className="text-xs text-slate-500">{proj.subtitle}</p>}
                    </div>
                    <button
                      onClick={() => handleDeleteProject(idx)}
                      className="p-1 text-slate-400 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  {proj.technologies?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {proj.technologies.map((t: string) => (
                        <Badge key={t} variant="neutral" className="text-[10px]">{t}</Badge>
                      ))}
                    </div>
                  )}
                  {proj.bullets?.length > 0 && (
                    <ul className="mt-2 list-disc list-inside text-xs text-slate-600 space-y-1">
                      {proj.bullets.map((b: string, bIdx: number) => (
                        <li key={bIdx}>{b}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 6: Conflicts & Audit */}
      {activeTab === 'conflicts' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Evidence Conflict Resolution & Traceability</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile.conflicts?.length === 0 ? (
              <div className="p-6 text-center text-emerald-700 bg-emerald-50 rounded-xl text-sm flex items-center justify-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                No data contradictions, chronology overlaps, or missing information detected across your source resumes.
              </div>
            ) : (
              profile.conflicts.map((conflict: any) => (
                <div
                  key={conflict.id}
                  className={`p-4 rounded-xl border ${
                    conflict.resolution_status === 'resolved'
                      ? 'border-emerald-200 bg-emerald-50/30'
                      : 'border-amber-200 bg-amber-50/30'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant={conflict.resolution_status === 'resolved' ? 'success' : 'warning'}>
                          {conflict.conflict_type}
                        </Badge>
                        <span className="text-xs text-slate-500 uppercase tracking-wider">{conflict.entity_type}</span>
                      </div>
                      <p className="text-sm font-medium text-slate-900 mt-2">{conflict.description}</p>
                      {conflict.resolution_notes && (
                        <p className="text-xs text-slate-500 mt-1 italic">Resolution note: {conflict.resolution_notes}</p>
                      )}
                    </div>
                    {conflict.resolution_status !== 'resolved' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setResolvingConflictId(conflict.id)
                          setResolutionStatus('resolved')
                        }}
                      >
                        Resolve
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Edit Contact Modal */}
      <Modal isOpen={showEditContact} onClose={() => setShowEditContact(false)} title="Update Candidate Details">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSaveContact()
          }}
          className="space-y-4"
        >
          <Input label="Full Name" value={contactForm.full_name} onChange={(e) => setContactForm({ ...contactForm, full_name: e.target.value })} required />
          <Input label="Email Address" type="email" value={contactForm.email} onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })} />
          <Input label="Phone Number" value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })} />
          <Input label="Location (City, Country)" value={contactForm.location} onChange={(e) => setContactForm({ ...contactForm, location: e.target.value })} />
          <Input label="Professional Headline" value={contactForm.headline} onChange={(e) => setContactForm({ ...contactForm, headline: e.target.value })} />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Executive Summary</label>
            <textarea
              rows={3}
              value={contactForm.summary}
              onChange={(e) => setContactForm({ ...contactForm, summary: e.target.value })}
              className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="LinkedIn URL" value={contactForm.linkedin_url} onChange={(e) => setContactForm({ ...contactForm, linkedin_url: e.target.value })} />
            <Input label="GitHub URL" value={contactForm.github_url} onChange={(e) => setContactForm({ ...contactForm, github_url: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowEditContact(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Save Changes</Button>
          </div>
        </form>
      </Modal>

      {/* Add Experience Modal */}
      <Modal isOpen={showAddExp} onClose={() => setShowAddExp(false)} title="Add Work Experience">
        <form onSubmit={handleCreateExperience} className="space-y-4">
          <Input label="Company Name" value={expForm.company} onChange={(e) => setExpForm({ ...expForm, company: e.target.value })} required />
          <Input label="Job Title" value={expForm.job_title} onChange={(e) => setExpForm({ ...expForm, job_title: e.target.value })} required />
          <Input label="Location" value={expForm.location} onChange={(e) => setExpForm({ ...expForm, location: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Start Date (MM/YYYY)" value={expForm.start_date} onChange={(e) => setExpForm({ ...expForm, start_date: e.target.value })} />
            <Input label="End Date (MM/YYYY)" value={expForm.end_date} onChange={(e) => setExpForm({ ...expForm, end_date: e.target.value })} disabled={expForm.is_current} />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input type="checkbox" checked={expForm.is_current} onChange={(e) => setExpForm({ ...expForm, is_current: e.target.checked })} className="rounded text-brand-600" />
            Currently working in this role
          </label>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Key Responsibilities / Impact</label>
            <textarea rows={3} value={expForm.description} onChange={(e) => setExpForm({ ...expForm, description: e.target.value })} className="w-full rounded-lg border border-slate-300 p-2.5 text-sm" />
          </div>
          <Input label="Skills Used (comma-separated)" value={expForm.skills_used} onChange={(e) => setExpForm({ ...expForm, skills_used: e.target.value })} placeholder="e.g. Python, FastAPI, Docker" />
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowAddExp(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Add Experience</Button>
          </div>
        </form>
      </Modal>

      {/* Add Education Modal */}
      <Modal isOpen={showAddEdu} onClose={() => setShowAddEdu(false)} title="Add Education Record">
        <form onSubmit={handleCreateEducation} className="space-y-4">
          <Input label="Institution / University" value={eduForm.institution} onChange={(e) => setEduForm({ ...eduForm, institution: e.target.value })} required />
          <Input label="Degree" value={eduForm.degree} onChange={(e) => setEduForm({ ...eduForm, degree: e.target.value })} placeholder="e.g. B.Tech, M.S." required />
          <Input label="Field of Study" value={eduForm.field_of_study} onChange={(e) => setEduForm({ ...eduForm, field_of_study: e.target.value })} placeholder="e.g. Computer Science" />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Start Year" value={eduForm.start_date} onChange={(e) => setEduForm({ ...eduForm, start_date: e.target.value })} />
            <Input label="End Year / Expected" value={eduForm.end_date} onChange={(e) => setEduForm({ ...eduForm, end_date: e.target.value })} />
          </div>
          <Input label="Grade / CGPA" value={eduForm.grade} onChange={(e) => setEduForm({ ...eduForm, grade: e.target.value })} placeholder="e.g. 3.8 GPA or 8.5 CGPA" />
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowAddEdu(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Add Education</Button>
          </div>
        </form>
      </Modal>

      {/* Add Skill Modal */}
      <Modal isOpen={showAddSkill} onClose={() => setShowAddSkill(false)} title="Add Technical Skill">
        <form onSubmit={handleCreateSkill} className="space-y-4">
          <Input label="Skill Name" value={skillForm.name} onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })} placeholder="e.g. PyTorch, Rust, AWS" required />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
            <select
              value={skillForm.category}
              onChange={(e) => setSkillForm({ ...skillForm, category: e.target.value })}
              className="w-full rounded-lg border border-slate-300 p-2.5 text-sm bg-white"
            >
              <option value="Languages">Languages</option>
              <option value="Backend">Backend</option>
              <option value="Frontend">Frontend</option>
              <option value="Cloud & DevOps">Cloud & DevOps</option>
              <option value="AI & Data">AI & Data</option>
              <option value="Databases">Databases</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Proficiency</label>
              <select
                value={skillForm.proficiency}
                onChange={(e) => setSkillForm({ ...skillForm, proficiency: e.target.value })}
                className="w-full rounded-lg border border-slate-300 p-2.5 text-sm bg-white"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
              </select>
            </div>
            <Input
              label="Years of Experience"
              type="number"
              step="0.5"
              value={skillForm.years_of_experience}
              onChange={(e) => setSkillForm({ ...skillForm, years_of_experience: Number(e.target.value) })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowAddSkill(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Add Skill</Button>
          </div>
        </form>
      </Modal>

      {/* Add Certification Modal */}
      <Modal isOpen={showAddCert} onClose={() => setShowAddCert(false)} title="Add Certification">
        <form onSubmit={handleCreateCert} className="space-y-4">
          <Input label="Certification Name" value={certForm.name} onChange={(e) => setCertForm({ ...certForm, name: e.target.value })} required />
          <Input label="Issuing Organization" value={certForm.issuing_organization} onChange={(e) => setCertForm({ ...certForm, issuing_organization: e.target.value })} placeholder="e.g. AWS, Google Cloud, Cisco" />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Issue Date" value={certForm.issue_date} onChange={(e) => setCertForm({ ...certForm, issue_date: e.target.value })} />
            <Input label="Expiry Date" value={certForm.expiry_date} onChange={(e) => setCertForm({ ...certForm, expiry_date: e.target.value })} />
          </div>
          <Input label="Credential URL" value={certForm.credential_url} onChange={(e) => setCertForm({ ...certForm, credential_url: e.target.value })} />
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowAddCert(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Add Certification</Button>
          </div>
        </form>
      </Modal>

      {/* Add Project Modal */}
      <Modal isOpen={showAddProject} onClose={() => setShowAddProject(false)} title="Add Portfolio Project">
        <form onSubmit={handleCreateProject} className="space-y-4">
          <Input label="Project Name" value={projectForm.name} onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })} required />
          <Input label="Subtitle / One-line Role" value={projectForm.subtitle} onChange={(e) => setProjectForm({ ...projectForm, subtitle: e.target.value })} placeholder="e.g. Open-source ATS Evaluation Engine" />
          <Input label="Technologies (comma-separated)" value={projectForm.technologies} onChange={(e) => setProjectForm({ ...projectForm, technologies: e.target.value })} placeholder="e.g. Python, FastAPI, PyTorch" />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Impact Bullets (one per line)</label>
            <textarea rows={3} value={projectForm.bullets} onChange={(e) => setProjectForm({ ...projectForm, bullets: e.target.value })} className="w-full rounded-lg border border-slate-300 p-2.5 text-sm" placeholder="Designed and implemented 7-dimension scoring engine" />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowAddProject(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Add Project</Button>
          </div>
        </form>
      </Modal>

      {/* Resolve Conflict Modal */}
      <Modal isOpen={resolvingConflictId !== null} onClose={() => setResolvingConflictId(null)} title="Resolve Evidence Conflict">
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Choose how you would like to mark this discrepancy across your source resumes:
          </p>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-800 cursor-pointer">
              <input type="radio" checked={resolutionStatus === 'resolved'} onChange={() => setResolutionStatus('resolved')} name="resStatus" />
              Mark as Resolved (verified accurate)
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-800 cursor-pointer">
              <input type="radio" checked={resolutionStatus === 'dismissed'} onChange={() => setResolutionStatus('dismissed')} name="resStatus" />
              Dismiss (ignore discrepancy)
            </label>
          </div>
          <Input
            label="Resolution Note"
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="e.g. Overlap is due to concurrent part-time consulting"
          />
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="ghost" onClick={() => setResolvingConflictId(null)}>Cancel</Button>
            <Button variant="primary" onClick={handleResolveConflict}>Save Resolution</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
