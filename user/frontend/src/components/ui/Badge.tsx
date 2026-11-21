import React from 'react'
import { cn } from '../../lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'neutral' | 'success' | 'warning' | 'error' | 'brand'
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'neutral',
  children,
  ...props
}) => {
  const variants = {
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    error: 'bg-red-50 text-red-700 border-red-200',
    brand: 'bg-brand-50 text-brand-700 border-brand-200',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
