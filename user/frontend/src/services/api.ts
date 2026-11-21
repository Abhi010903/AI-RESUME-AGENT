// Centralized API client for Candidate Platform

const API_BASE = '/api/v1'

export interface ApiError {
  message: string
  code?: string
  status?: number
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token')
  const headers = new Headers(options.headers || {})

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (response.status === 204) {
    return {} as T
  }

  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred'
    try {
      const errJson = await response.json()
      errorDetail = errJson.detail || (errJson.error && errJson.error.message) || JSON.stringify(errJson)
    } catch {
      errorDetail = response.statusText || `Request failed with status ${response.status}`
    }

    if (response.status === 401 && !endpoint.includes('/auth/login')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    throw new Error(errorDetail)
  }

  return response.json()
}

export const api = {
  // Auth
  auth: {
    register: (data: { email: string; password: string; full_name: string }) =>
      request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      request<{ access_token: string; token_type: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getMe: () => request<any>('/auth/me'),
    updateMe: (data: { full_name?: string }) =>
      request<any>('/auth/me', { method: 'PATCH', body: JSON.stringify(data) }),
    changePassword: (data: { current_password: string; new_password: string }) =>
      request<any>('/auth/password-change', { method: 'POST', body: JSON.stringify(data) }),
    requestPasswordReset: (data: { email: string }) =>
      request<any>('/auth/password-reset/request', { method: 'POST', body: JSON.stringify(data) }),
    confirmPasswordReset: (data: { token: string; new_password: string }) =>
      request<any>('/auth/password-reset/confirm', { method: 'POST', body: JSON.stringify(data) }),
    logout: () => request<any>('/auth/logout', { method: 'POST' }),
    deleteAccount: () => request<any>('/auth/me', { method: 'DELETE' }),
    exportData: () => request<any>('/auth/export-data'),
  },

  // Candidate Workflow Engine & Activity
  workflow: {
    status: () => request<any>('/workflow/status'),
    activity: (limit = 20) => request<any[]>(`/workflow/activity?limit=${limit}`),
  },

  // Resumes / Documents Ingestion
  resumes: {
    uploadBatch: (files: File[]) => {
      const formData = new FormData()
      files.forEach((file) => formData.append('files', file))
      return request<any>('/resumes/upload', { method: 'POST', body: formData })
    },
    list: (limit = 50, offset = 0) =>
      request<any[]>(`/resumes?limit=${limit}&offset=${offset}`),
    get: (id: string) => request<any>(`/resumes/${id}`),
    getText: (id: string) => request<any>(`/resumes/${id}/text`),
    downloadUrl: (id: string) => `${API_BASE}/resumes/${id}/download`,
    reprocess: (id: string) => request<any>(`/resumes/${id}/reprocess`, { method: 'POST' }),
    delete: (id: string) => request<any>(`/resumes/${id}`, { method: 'DELETE' }),
  },

  // Candidate Profiles
  profiles: {
    list: () => request<any[]>('/profiles'),
    get: (id: string) => request<any>(`/profiles/${id}`),
    consolidate: (documentIds: string[]) =>
      request<any>('/profiles/consolidate', {
        method: 'POST',
        body: JSON.stringify({ document_ids: documentIds }),
      }),
    update: (id: string, data: any) =>
      request<any>(`/profiles/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    approve: (id: string, data: any) =>
      request<any>(`/profiles/${id}/approve`, { method: 'POST', body: JSON.stringify(data) }),
    resolveConflict: (profileId: string, conflictId: string, data: any) =>
      request<any>(`/profiles/${profileId}/conflicts/${conflictId}/resolve`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    // Items
    addExperience: (profileId: string, data: any) =>
      request<any>(`/profiles/${profileId}/experiences`, { method: 'POST', body: JSON.stringify(data) }),
    deleteExperience: (profileId: string, expId: string) =>
      request<any>(`/profiles/${profileId}/experiences/${expId}`, { method: 'DELETE' }),
    addEducation: (profileId: string, data: any) =>
      request<any>(`/profiles/${profileId}/education`, { method: 'POST', body: JSON.stringify(data) }),
    deleteEducation: (profileId: string, eduId: string) =>
      request<any>(`/profiles/${profileId}/education/${eduId}`, { method: 'DELETE' }),
    addSkill: (profileId: string, data: any) =>
      request<any>(`/profiles/${profileId}/skills`, { method: 'POST', body: JSON.stringify(data) }),
    deleteSkill: (profileId: string, skillId: string) =>
      request<any>(`/profiles/${profileId}/skills/${skillId}`, { method: 'DELETE' }),
    addCertification: (profileId: string, data: any) =>
      request<any>(`/profiles/${profileId}/certifications`, { method: 'POST', body: JSON.stringify(data) }),
    deleteCertification: (profileId: string, certId: string) =>
      request<any>(`/profiles/${profileId}/certifications/${certId}`, { method: 'DELETE' }),
    addProject: (profileId: string, data: any) =>
      request<any>(`/profiles/${profileId}/projects`, { method: 'POST', body: JSON.stringify(data) }),
    updateProject: (profileId: string, index: number, data: any) =>
      request<any>(`/profiles/${profileId}/projects/${index}`, { method: 'PATCH', body: JSON.stringify(data) }),
    deleteProject: (profileId: string, index: number) =>
      request<any>(`/profiles/${profileId}/projects/${index}`, { method: 'DELETE' }),
    delete: (id: string) => request<any>(`/profiles/${id}`, { method: 'DELETE' }),
  },

  // Job Descriptions
  jobs: {
    analyze: (rawText: string, metadata?: { title?: string; company?: string; location?: string }) =>
      request<any>('/jobs/analyze', {
        method: 'POST',
        body: JSON.stringify({ raw_text: rawText, ...metadata }),
      }),
    upload: (file: File, metadata?: { title?: string; company?: string; location?: string }) => {
      const formData = new FormData()
      formData.append('file', file)
      if (metadata?.title) formData.append('title', metadata.title)
      if (metadata?.company) formData.append('company', metadata.company)
      if (metadata?.location) formData.append('location', metadata.location)
      return request<any>('/jobs/upload', { method: 'POST', body: formData })
    },
    list: (limit = 50, offset = 0) =>
      request<any[]>(`/jobs?limit=${limit}&offset=${offset}`),
    get: (id: string) => request<any>(`/jobs/${id}`),
    update: (id: string, data: any) =>
      request<any>(`/jobs/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    getRequirements: (id: string) => request<any>(`/jobs/${id}/requirements`),
    getSkills: (id: string) => request<any>(`/jobs/${id}/skills`),
    delete: (id: string) => request<any>(`/jobs/${id}`, { method: 'DELETE' }),
  },

  // Matching Engine
  matches: {
    create: (data: { profile_id: string; job_id: string }) =>
      request<any>('/matches', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: string) => request<any>(`/matches/${id}`),
    list: (limit = 50, offset = 0) =>
      request<any[]>(`/matches?limit=${limit}&offset=${offset}`),
  },

  // Resume Generation
  generation: {
    generate: (data: { profile_id: string; job_id: string; match_id?: string; title?: string }) =>
      request<any>('/resumes/generate', { method: 'POST', body: JSON.stringify(data) }),
    list: (limit = 50, offset = 0) =>
      request<any[]>(`/resumes/generated?limit=${limit}&offset=${offset}`),
    get: (id: string) => request<any>(`/resumes/generated/${id}`),
    getVersions: (id: string) => request<any>(`/resumes/generated/${id}/versions`),
    downloadUrl: (id: string, format: 'pdf' | 'docx' = 'pdf') =>
      `${API_BASE}/resumes/generated/${id}/download?format=${format}`,
    delete: (id: string) => request<any>(`/resumes/generated/${id}`, { method: 'DELETE' }),
  },

  // ATS Evaluation
  ats: {
    evaluate: (data: { resume_id: string; job_id: string }) =>
      request<any>('/ats/evaluate', { method: 'POST', body: JSON.stringify(data) }),
    getReport: (id: string) => request<any>(`/ats/reports/${id}`),
    list: (resumeId?: string) =>
      request<any[]>(`/ats/reports${resumeId ? `?resume_id=${resumeId}` : ''}`),
  },

  // Application Tracking
  applications: {
    create: (data: any) =>
      request<any>('/applications', { method: 'POST', body: JSON.stringify(data) }),
    list: (status?: string, search?: string) => {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      if (search) params.append('search', search)
      return request<any[]>(`/applications?${params.toString()}`)
    },
    get: (id: string) => request<any>(`/applications/${id}`),
    update: (id: string, data: any) =>
      request<any>(`/applications/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: string) => request<any>(`/applications/${id}`, { method: 'DELETE' }),
  },
}
