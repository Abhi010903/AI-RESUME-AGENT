import React from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import {
  FileText,
  User,
  Briefcase,
  GitCompare,
  Wand2,
  CheckCircle2,
  Kanban,
  Settings,
  LogOut,
  LayoutDashboard,
  Layers,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'

export const AppLayout: React.FC = () => {
  const location = useLocation()
  const { user, logout } = useAuth()

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Resumes & Ingestion', path: '/resumes', icon: FileText },
    { label: 'Candidate Profile', path: '/profile', icon: User },
    { label: 'Target Jobs', path: '/jobs', icon: Briefcase },
    { label: 'Skill Match Engine', path: '/matching', icon: GitCompare },
    { label: 'Resume Builder', path: '/generation', icon: Wand2 },
    { label: 'ATS Evaluation', path: '/ats', icon: CheckCircle2 },
    { label: 'Application Tracker', path: '/applications', icon: Kanban },
    { label: 'Settings', path: '/settings', icon: Settings },
  ]

  return (
    <div className="flex h-screen w-full bg-slate-50 text-slate-800 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0 z-20">
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800/80">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center text-white shadow-md">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-white text-base tracking-tight">AI Resume Agent</span>
            <span className="block text-[10px] text-slate-400 font-medium uppercase tracking-wider">Candidate Platform</span>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                )}
              >
                <Icon className={cn('w-4 h-4', isActive ? 'text-white' : 'text-slate-400')} />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* User Card */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-brand-700 text-white flex items-center justify-center text-xs font-bold uppercase flex-shrink-0">
                {user?.full_name ? user.full_name[0] : 'U'}
              </div>
              <div className="truncate">
                <p className="text-sm font-medium text-slate-200 truncate">{user?.full_name || 'Candidate'}</p>
                <p className="text-xs text-slate-400 truncate">{user?.email || 'Logged in'}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className="h-16 bg-white border-b border-slate-200/80 px-8 flex items-center justify-between flex-shrink-0 z-10">
          <h2 className="text-lg font-semibold text-slate-800">
            {navItems.find((item) => item.path === location.pathname)?.label || 'Candidate Platform'}
          </h2>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              API Connected
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
