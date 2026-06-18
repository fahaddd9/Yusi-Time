'use client'
/**
 * TimerBar — Implementation Plan §4.14 · Blueprint v2.0 G3.
 *
 * Mounted in the app shell layout above <main>. Visible when:
 *   - Timer is running (shows elapsed counter + Stop button)
 *   - Timer is not running (shows project selector + Start button)
 *
 * Elapsed counter uses tabular-nums (font-mono) to prevent layout
 * reflow as digits increment (Blueprint §4.14).
 *
 * Idle state: shows amber "Idle Xm" pill, elapsed text turns amber.
 * Idle detector only mounts when a timer is running AND idle detection
 * is enabled in workspace settings.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { Play, Square, Clock, DollarSign } from 'lucide-react'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useTimerStore } from '@/stores/timer-store'
import { useCurrentTimer, useStartTimer, useStopTimer } from '@/features/time-entries/hooks'
import { useIdleDetector } from '@/features/timer/hooks/useIdleDetector'
import { useDescriptionDraft } from '@/features/timer/hooks/useDescriptionDraft'
import { useMe, useWorkspace } from '@/features/settings/hooks'
import { useProjects, useTasks, useTags } from '@/features/projects/hooks'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu'
import { Tag as TagIcon } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { cn } from '@/lib/utils'

function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  const hh = String(h).padStart(2, '0')
  const mm = String(m).padStart(2, '0')
  const ss = String(s).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

export function TimerBar() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { isIdle, idleStartTime } = useTimerStore()
  const { data: currentEntry, isLoading } = useCurrentTimer(activeWorkspaceId)
  const { data: user } = useMe()
  const { data: workspaceDetail } = useWorkspace(activeWorkspaceId)

  const startTimer = useStartTimer(activeWorkspaceId ?? '')
  const stopTimer = useStopTimer(activeWorkspaceId ?? '')

  const [elapsed, setElapsed] = useState(0)
  const [description, setDescription] = useState('')
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([])
  const [billable, setBillable] = useState(true)
  const [showSwitchDialog, setShowSwitchDialog] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Fetch projects and tasks
  const { data: projectsData } = useProjects()
  const projects = (projectsData?.data ?? []).filter((p) => p.status === 'active')
  const { data: tasksData } = useTasks(selectedProjectId ?? undefined)
  const tasks = tasksData?.data ?? []
  const { data: tagsData } = useTags()
  const tags = tagsData ?? []

  // Auto-sync billable toggle based on hierarchy: Task override > Project default
  useEffect(() => {
    if (currentEntry) return; // Don't sync while running, it's locked to the active entry

    if (selectedProjectId) {
      const project = projects.find((p) => p.id === selectedProjectId);
      let nextBillable = project?.default_billable ?? true;

      if (selectedTaskId) {
        const task = tasks.find((t) => t.id === selectedTaskId);
        if (task && task.billable_override !== null && task.billable_override !== undefined) {
          nextBillable = task.billable_override;
        }
      }
      setBillable(nextBillable);
    }
  }, [selectedProjectId, selectedTaskId, projects, tasks, currentEntry]);

  // Get workspace idle settings from WorkspaceDetail (has idle_detection_enabled)
  const idleEnabled = workspaceDetail?.idle_detection_enabled ?? false
  const idleTimeoutMs = (workspaceDetail?.idle_timeout_minutes ?? 15) * 60_000

  // Draft hook
  const { getDraft, saveDraft, clearDraft } = useDescriptionDraft({
    userId: user?.id ?? '',
    workspaceId: activeWorkspaceId ?? '',
  })

  // Restore description draft on mount (only when no active timer)
  useEffect(() => {
    if (!currentEntry) {
      setDescription(getDraft())
    }
  }, [currentEntry]) // eslint-disable-line react-hooks/exhaustive-deps

  // Sync description with active entry
  useEffect(() => {
    if (currentEntry) {
      setDescription(currentEntry.description ?? '')
    }
  }, [currentEntry?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  // Elapsed counter — live tick from start_time
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)

    if (!currentEntry?.start_time) {
      setElapsed(0)
      return
    }

    const tick = () => {
      const start = new Date(currentEntry.start_time).getTime()
      setElapsed(Math.max(0, Math.floor((Date.now() - start) / 1000)))
    }

    tick() // immediate
    intervalRef.current = setInterval(tick, 1000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [currentEntry?.start_time])

  // Idle detector — only active when timer is running AND workspace enables it
  useIdleDetector({
    timeoutMs: idleTimeoutMs,
    enabled: !!currentEntry && idleEnabled,
  })

  // Idle pill elapsed (minutes since idle began)
  const idleMinutes = idleStartTime
    ? Math.floor((Date.now() - idleStartTime.getTime()) / 60_000)
    : 0

  const doStartTimer = useCallback(async (force: boolean) => {
    if (!selectedProjectId) return
    await startTimer.mutateAsync({
      project_id: selectedProjectId,
      task_id: selectedTaskId,
      description: description.trim() || null,
      billable,
      tag_ids: selectedTagIds.length > 0 ? selectedTagIds : undefined,
      force,
    })
    clearDraft()
    setDescription('')
    setShowSwitchDialog(false)
  }, [selectedProjectId, selectedTaskId, description, billable, selectedTagIds, startTimer, clearDraft])

  const handleStart = useCallback(async () => {
    if (!selectedProjectId) return
    if (currentEntry) {
      setShowSwitchDialog(true)
      return
    }
    await doStartTimer(false)
  }, [selectedProjectId, currentEntry, doStartTimer])

  const handleStop = useCallback(async () => {
    if (!currentEntry) return
    await stopTimer.mutateAsync({
      entryId: currentEntry.id,
      payload: {},
    })
    clearDraft()
    setDescription('')
  }, [currentEntry, stopTimer, clearDraft])

  const isRunning = !!currentEntry
  const isCurrentProjectRunning = isRunning && currentEntry.project_id === selectedProjectId

  if (isLoading || !activeWorkspaceId) return null

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-2.5 border-b border-border bg-card',
        'transition-colors duration-200',
        isIdle && 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800',
      )}
      role="toolbar"
      aria-label="Time tracker"
    >
      {/* ── Elapsed / Idle indicator ── */}
      <div className="flex items-center gap-2 min-w-[80px]">
        <Clock
          className={cn(
            'w-4 h-4 flex-shrink-0',
            isRunning && !isIdle && 'text-[#F06900]',
            isIdle && 'text-amber-500',
            !isRunning && 'text-muted-foreground',
          )}
        />
        <span
          className={cn(
            'font-mono text-sm tabular-nums font-medium',
            isRunning && !isIdle && 'text-[#F06900]',
            isIdle && 'text-amber-500',
            !isRunning && 'text-muted-foreground',
          )}
        >
          {formatElapsed(elapsed)}
        </span>
        {isIdle && (
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400">
            Idle {idleMinutes}m
          </span>
        )}
      </div>

      {/* ── Description input ── */}
      <input
        type="text"
        id="timer-description"
        placeholder="What are you working on?"
        value={description}
        onChange={(e) => {
          setDescription(e.target.value)
          saveDraft(e.target.value)
        }}
        disabled={isRunning}
        className={cn(
          'flex-1 min-w-[200px] text-sm bg-transparent outline-none placeholder:text-muted-foreground/60',
          'border-b border-transparent focus:border-border transition-colors',
          'disabled:cursor-default disabled:opacity-70',
        )}
        aria-label="Timer description"
        maxLength={500}
      />

      {/* ── Project / Task Selectors (Always visible) ── */}
      <div className="flex items-center gap-2">
          <Select value={selectedProjectId ?? ''} onValueChange={setSelectedProjectId}>
            <SelectTrigger className="w-[160px] border-none bg-accent/50 hover:bg-accent">
              <SelectValue placeholder="Select project…" className="min-w-0">
                {selectedProjectId && projects.find((p) => p.id === selectedProjectId) ? (
                  <div className="flex items-center gap-2 overflow-hidden min-w-0 w-full">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: projects.find((p) => p.id === selectedProjectId)?.color ?? '#ccc' }}
                    />
                    <span className="truncate block flex-1 text-left">{projects.find((p) => p.id === selectedProjectId)?.name}</span>
                  </div>
                ) : (
                  'Select project…'
                )}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {projects.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: p.color ?? '#ccc' }}
                    />
                    <span className="truncate">{p.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={selectedTaskId ?? ''}
            onValueChange={setSelectedTaskId}
            disabled={!selectedProjectId || tasks.length === 0}
          >
            <SelectTrigger className="w-[140px] border-none bg-accent/50 hover:bg-accent">
              <SelectValue placeholder="Select task…" className="min-w-0">
                {selectedTaskId && tasks.find((t) => t.id === selectedTaskId) ? (
                  <span className="truncate block w-full text-left">{tasks.find((t) => t.id === selectedTaskId)?.name}</span>
                ) : (
                  'Select task…'
                )}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {tasks.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* ── Tags Selector ── */}
          <DropdownMenu>
            <DropdownMenuTrigger render={<button />}>
              <button
                type="button"
                disabled={isRunning || tags.length === 0}
                className={cn(
                  'flex items-center justify-center p-1.5 rounded-md transition-colors',
                  selectedTagIds.length > 0
                    ? 'text-brand-orange bg-brand-orange/10'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                  'disabled:cursor-default disabled:opacity-50'
                )}
                title={selectedTagIds.length > 0 ? `${selectedTagIds.length} tags selected` : 'Select tags'}
              >
                <TagIcon className="w-4 h-4" />
                {selectedTagIds.length > 0 && (
                  <span className="ml-1.5 text-xs font-medium">{selectedTagIds.length}</span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[200px]">
              {tags.map((tag) => (
                <DropdownMenuCheckboxItem
                  key={tag.id}
                  checked={selectedTagIds.includes(tag.id)}
                  onCheckedChange={(checked) => {
                    setSelectedTagIds((prev) =>
                      checked ? [...prev, tag.id] : prev.filter((id) => id !== tag.id)
                    )
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: tag.color ?? '#ccc' }}
                    />
                    <span className="truncate">{tag.name}</span>
                  </div>
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

      {/* ── Billable toggle ── */}
      <button
        id="timer-billable-toggle"
        type="button"
        title={billable ? 'Billable — click to toggle' : 'Non-billable — click to toggle'}
        onClick={() => setBillable((b) => !b)}
        disabled={isRunning}
        className={cn(
          'p-1.5 rounded-md transition-colors',
          billable
            ? 'text-[#F06900] bg-[#FFF0E6] dark:bg-orange-900/20'
            : 'text-muted-foreground hover:text-foreground',
          'disabled:cursor-default disabled:opacity-60',
        )}
        aria-pressed={billable}
        aria-label={billable ? 'Billable' : 'Non-billable'}
      >
        <DollarSign className="w-4 h-4" />
      </button>

      {/* ── Start / Stop button ── */}
      {isCurrentProjectRunning ? (
        <button
          id="timer-stop-button"
          type="button"
          onClick={handleStop}
          disabled={stopTimer.isPending}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold',
            'bg-destructive text-white hover:bg-destructive/90 transition-colors',
            'disabled:opacity-60 disabled:cursor-not-allowed',
          )}
          aria-label="Stop timer"
        >
          <Square className="w-3.5 h-3.5 fill-current" />
          Stop
        </button>
      ) : (
        <button
          id="timer-start-button"
          type="button"
          onClick={handleStart}
          disabled={!selectedProjectId || startTimer.isPending}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold',
            'bg-[#F06900] text-white hover:bg-[#D95E00] transition-colors',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          )}
          aria-label="Start timer"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          Start
        </button>
      )}

      {/* ── Running entry info (project name / billable amount) ── */}
      {isRunning && currentEntry && (
        <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground border-l border-border pl-3">
          <span
            className="inline-block w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: currentEntry.project_color ?? '#6B7280' }}
          />
          <span className="truncate max-w-[140px]">{currentEntry.project_name}</span>
          {currentEntry.billable_amount && (
            <span className="font-medium text-[#F06900]">${currentEntry.billable_amount}</span>
          )}
        </div>
      )}

      {/* ── Switch Timer Confirmation Dialog ── */}
      <AlertDialog open={showSwitchDialog} onOpenChange={setShowSwitchDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Switch active timer?</AlertDialogTitle>
            <AlertDialogDescription>
              A timer is already running for <strong>{currentEntry?.project_name}</strong>. Starting a new timer will automatically stop the current one and save its tracked time.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-[#F06900] text-white hover:bg-[#D95E00]"
              onClick={() => doStartTimer(true)}
            >
              Start New Timer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
