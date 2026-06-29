'use client'
/**
 * WorkStartModal — Phase 6.5, Addendum §6.1 (F1).
 *
 * NON-DISMISSIBLE (identical pattern to IdleModal — no X, no backdrop click,
 * no Escape key) per Addendum §6.1 / human supervisor decision 2026-06-21.
 *
 * Two attendance mode variants (one component, different copy):
 *
 *   Fixed Schedule mode — two states:
 *     On-time:  "Time to start working — shall we begin tracking?"
 *     Late:     "You are {X} late — shall we start tracking?"
 *
 *   Flexible Hours mode — one state only:
 *     "Still time to log hours today — start tracking?"
 *     No late-arrival language (PRD-ADD-02b, PRD-ADD-08).
 *
 * Two choices:
 *   1. "Start Tracking"  — reveals inline project/task selector, then calls
 *                          POST /time-entries/work-start-response { response:"start" }
 *   2. "Not Now"         — calls POST { response:"not_now" }, closes immediately
 *
 * The modal is opened by the WorkStartTrigger (useWorkStartTrigger hook in
 * useAttendance.ts) which reads unread attendance notifications from the
 * attendance notification polling query. It is mounted in (app)/layout.tsx
 * alongside IdleModal.
 *
 * PRD-ADD-03: Only Member role ever opens this modal. The trigger hook
 * suppresses itself for Admin/Manager roles.
 */

import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { Loader2, Clock, Play, X, ChevronDown, Timer } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useAttendanceStore } from '@/stores/attendance-store'
import { useWorkStartResponse } from '@/features/attendance/hooks/useAttendance'
import { useProjects } from '@/features/projects/hooks'
import type { Project } from '@/features/projects/types'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatLate(minutes: number): string {
  if (minutes < 60) return `${minutes}m late`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}m late` : `${h}h late`
}

// ── ProjectSelector — inline, no extra modal ──────────────────────────────────

interface ProjectSelectorProps {
  projects: Project[]
  selectedId: string | null
  onSelect: (id: string) => void
  disabled: boolean
}

function ProjectSelector({ projects, selectedId, onSelect, disabled }: ProjectSelectorProps) {
  const [open, setOpen] = useState(false)
  const selected = projects.find((p) => p.id === selectedId)

  return (
    <div className="relative">
      <button
        id="work-start-project-selector"
        type="button"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg',
          'border border-border bg-muted/40 hover:bg-muted/60 transition-colors',
          'text-sm disabled:opacity-50 disabled:cursor-not-allowed',
          !selectedId && 'text-muted-foreground'
        )}
      >
        <span className="truncate">{selected ? selected.name : 'Select a project…'}</span>
        <ChevronDown className={cn('w-4 h-4 shrink-0 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-full max-h-44 overflow-y-auto rounded-lg border border-border bg-popover shadow-lg">
          {projects.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">No projects found</p>
          ) : (
            projects.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  onSelect(p.id)
                  setOpen(false)
                }}
                className={cn(
                  'w-full px-3 py-2 text-sm text-left hover:bg-muted/50 transition-colors',
                  selectedId === p.id && 'bg-[#FFF3EA] dark:bg-orange-900/20 text-[#FE6900] font-medium'
                )}
              >
                {p.name}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}

// ── WorkStartModal ─────────────────────────────────────────────────────────────

export function WorkStartModal() {
  const { workStartOpen, workStartContext, closeWorkStart } = useAttendanceStore()
  const workspaceId = workStartContext?.workspace_id ?? ''

  const workStartResponse = useWorkStartResponse(workspaceId)
  const { data: projectsData } = useProjects({ status: 'active' })
  const projects: Project[] = (projectsData as any)?.data ?? projectsData ?? []

  // UI state
  const [showProjectSelector, setShowProjectSelector] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [pendingAction, setPendingAction] = useState<'start' | 'not_now' | null>(null)

  // Reset selector state when modal closes/opens
  useEffect(() => {
    if (!workStartOpen) {
      setShowProjectSelector(false)
      setSelectedProjectId(null)
      setPendingAction(null)
    }
  }, [workStartOpen])

  const isLoading = pendingAction !== null
  const mode = workStartContext?.attendance_mode ?? 'fixed_schedule'
  const lateMinutes = workStartContext?.late_by_minutes ?? null
  const isLate = mode === 'fixed_schedule' && lateMinutes !== null && lateMinutes > 0

  // ── Copy ───────────────────────────────────────────────────────────────────
  const title =
    mode === 'flexible_hours'
      ? 'Still time to log hours today'
      : isLate
        ? `You're ${formatLate(lateMinutes!)} — ready to start?`
        : 'Time to start working'

  const description =
    mode === 'flexible_hours'
      ? "You haven't logged any time today. Start tracking to make progress toward your daily target."
      : isLate
        ? 'Your scheduled start time has passed. Would you like to begin tracking now?'
        : "Your scheduled work time has arrived. Shall we begin tracking your time?"

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleStartClick = () => {
    // First click: show project selector
    if (!showProjectSelector) {
      setShowProjectSelector(true)
      return
    }
    // Second click (after project selected): confirm + call API
    if (!selectedProjectId) {
      toast.error('Please select a project to start tracking')
      return
    }
    handleConfirmStart()
  }

  const handleConfirmStart = async () => {
    if (!selectedProjectId || !workspaceId) return
    setPendingAction('start')
    try {
      await workStartResponse.mutateAsync({
        response: 'start',
        project_id: selectedProjectId,
      })
      toast.success('Timer started!')
      closeWorkStart()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to start timer')
    } finally {
      setPendingAction(null)
    }
  }

  const handleNotNow = async () => {
    if (!workspaceId) return
    setPendingAction('not_now')
    try {
      await workStartResponse.mutateAsync({ response: 'not_now' })
      closeWorkStart()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Something went wrong')
    } finally {
      setPendingAction(null)
    }
  }

  return (
    <Dialog open={workStartOpen} onOpenChange={() => {}}>
      <DialogContent
        className="sm:max-w-sm"
        showCloseButton={false}
        nonDismissible
        onKeyDown={(e: React.KeyboardEvent) => {
          if (e.key === 'Escape') {
            e.preventDefault()
            e.stopPropagation()
          }
        }}
      >
        {/* Header */}
        <DialogHeader>
          <DialogTitle
            className={cn(
              'flex items-center gap-2',
              isLate
                ? 'text-amber-600 dark:text-amber-400'
                : 'text-[#FE6900]'
            )}
          >
            {isLate ? (
              <Clock className="w-5 h-5 shrink-0" />
            ) : (
              <Timer className="w-5 h-5 shrink-0" />
            )}
            {title}
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {description}
          </DialogDescription>
        </DialogHeader>

        {/* Mode badge */}
        <div className="flex items-center gap-1.5 mt-0.5">
          <span
            className={cn(
              'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
              mode === 'fixed_schedule'
                ? 'bg-[#FFF3EA] dark:bg-orange-900/20 text-[#FE6900]'
                : 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
            )}
          >
            {mode === 'fixed_schedule' ? 'Fixed Schedule' : 'Flexible Hours'}
          </span>
          {isLate && lateMinutes !== null && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400">
              {formatLate(lateMinutes)}
            </span>
          )}
        </div>

        {/* Inline project selector — appears when "Start Tracking" is clicked */}
        {showProjectSelector && (
          <div className="mt-2 space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Select Project
            </p>
            <ProjectSelector
              projects={projects}
              selectedId={selectedProjectId}
              onSelect={setSelectedProjectId}
              disabled={isLoading}
            />
            {selectedProjectId && (
              <p className="text-xs text-muted-foreground">
                Ready to start — click{' '}
                <span className="font-medium text-[#FE6900]">Start Tracking</span> to confirm.
              </p>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-col gap-2.5 mt-3">
          {/* Start Tracking — primary CTA */}
          <button
            id="work-start-modal-start"
            type="button"
            onClick={handleStartClick}
            disabled={isLoading || (showProjectSelector && !selectedProjectId)}
            className={cn(
              'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg',
              'bg-[#FE6900] hover:bg-[#E55E00] active:scale-[0.98]',
              'text-white text-sm font-semibold transition-all duration-150',
              'disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100'
            )}
          >
            {pendingAction === 'start' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-white" />
            )}
            {showProjectSelector && selectedProjectId
              ? 'Confirm & Start Tracking'
              : showProjectSelector
                ? 'Select a project above'
                : 'Start Tracking'}
          </button>

          {/* Not Now — secondary */}
          <button
            id="work-start-modal-not-now"
            type="button"
            onClick={handleNotNow}
            disabled={isLoading}
            className={cn(
              'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg',
              'border border-border bg-card hover:bg-muted/50 transition-colors',
              'text-sm font-medium text-muted-foreground',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {pendingAction === 'not_now' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <X className="w-4 h-4" />
            )}
            Not Now
          </button>
        </div>

        {/* Footer note — no re-prompt guarantee */}
        <p className="text-xs text-muted-foreground text-center mt-1">
          Choosing &quot;Not Now&quot; won&apos;t show this prompt again today.
        </p>
      </DialogContent>
    </Dialog>
  )
}
