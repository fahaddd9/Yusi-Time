import * as React from 'react'
import { cn } from '@/lib/utils'
import { ScrollReveal } from './scroll-reveal'

export function PageHeader({ title, description, children }: { title: string; description?: string; children?: React.ReactNode }) {
  return (
    <ScrollReveal distance={20} duration={0.6}>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground tracking-tight">{title}</h2>
          {description && <p className="text-[14px] text-muted-foreground mt-1">{description}</p>}
        </div>
        {children && <div>{children}</div>}
      </div>
    </ScrollReveal>
  )
}

export interface SettingRowProps {
  label: string
  description?: React.ReactNode
  children: React.ReactNode
  disabled?: boolean
  className?: string
  index?: number // Used for staggering multiple rows
}

export function SettingRow({ label, description, children, disabled = false, className, index = 0 }: SettingRowProps) {
  return (
    <ScrollReveal staggerIndex={index} distance={30}>
      <div
        className={cn(
          "flex flex-col sm:flex-row sm:items-center justify-between gap-6 p-6 bg-white dark:bg-card border border-border/60 rounded-2xl shadow-sm transition-all duration-300 hover:shadow-md hover:border-brand-orange/30 group",
          disabled && "opacity-60 pointer-events-none",
          className
        )}
      >
        <div className="flex-1 min-w-0 pr-4">
          <label className={cn("text-[15px] font-semibold tracking-tight", disabled ? "text-muted-foreground" : "text-foreground")}>
            {label}
          </label>
          {description && (
            <p className="text-[14px] text-muted-foreground mt-1.5 leading-relaxed">
              {description}
            </p>
          )}
        </div>
        <div className="mt-3 sm:mt-0 w-full sm:w-[320px] lg:w-[400px] flex-shrink-0 flex items-center sm:justify-end">
          <div className="w-full flex items-center sm:justify-end">{children}</div>
        </div>
      </div>
    </ScrollReveal>
  )
}
