'use client'
/**
 * IdleModal — Implementation Plan §4.15 · Blueprint v2.0 G4.
 *
 * NON-DISMISSIBLE (no X, no backdrop click, no Escape key) per spec.
 * Opens automatically when the idle detector fires via ui-store.
 *
 * Three options:
 *   1. Keep Time & Continue — clears idle state, leaves timer running (idle time included)
 *   2. Discard Idle & Stop — stops timer with idle_end_time (trim the idle period)
 *   3. Discard Idle & Continue — stops timer with idle_end_time, starts NEW timer instantly
 *
 * Loading state: all three buttons disabled + spinner while mutation is in-flight.
 * Error state:   all three buttons re-enabled + toast.error() for the failure.
 */

import { useState } from 'react'
import { toast } from 'sonner'
import { Loader2, Clock, Scissors, Play } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useTimerStore } from '@/stores/timer-store'
import { useUIStore } from '@/stores/ui-store'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useCurrentTimer, useStopTimer, useStartTimer } from '@/features/time-entries/hooks'
import { formatDuration } from '@/lib/utils'
import { cn } from '@/lib/utils'

type Action = 'keep-continue' | 'discard-stop' | 'discard-continue' | null

export function IdleModal() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { isIdle, idleStartTime, clearIdle } = useTimerStore()
  const { closeModal } = useUIStore()
  const { data: currentEntry } = useCurrentTimer(activeWorkspaceId)
  const stopTimer = useStopTimer(activeWorkspaceId ?? '')

  const startTimer = useStartTimer(activeWorkspaceId ?? '')

  const [pendingAction, setPendingAction] = useState<Action>(null)

  const idleSeconds = idleStartTime
    ? Math.floor((Date.now() - idleStartTime.getTime()) / 1000)
    : 0

  const handleKeepAndContinue = () => {
    // User wants to keep tracking and include the idle time
    clearIdle()
    closeModal()
  }

  const handleDiscardAndStop = async () => {
    if (!currentEntry || !activeWorkspaceId || !idleStartTime) return
    setPendingAction('discard-stop')
    try {
      await stopTimer.mutateAsync({
        entryId: currentEntry.id,
        payload: { idle_end_time: idleStartTime.toISOString() },
      })
      clearIdle()
      closeModal()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to stop timer')
    } finally {
      setPendingAction(null)
    }
  }

  const handleDiscardAndContinue = async () => {
    if (!currentEntry || !activeWorkspaceId || !idleStartTime) return
    setPendingAction('discard-continue')
    try {
      // 1. Stop old timer at idle start
      await stopTimer.mutateAsync({
        entryId: currentEntry.id,
        payload: { idle_end_time: idleStartTime.toISOString() },
      })
      
      // 2. Start a new timer matching the old one
      await startTimer.mutateAsync({
        project_id: currentEntry.project_id,
        task_id: currentEntry.task_id,
        description: currentEntry.description,
        billable: currentEntry.billable,
        force: true,
      })
      
      clearIdle()
      closeModal()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to process timer')
    } finally {
      setPendingAction(null)
    }
  }



  const isLoading = pendingAction !== null
  const isOpen = isIdle && !!currentEntry

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent
        className="sm:max-w-sm"
        showCloseButton={false}
        nonDismissible
        onKeyDown={(e: React.KeyboardEvent) => {
          // Prevent Escape from closing the modal — user must choose an option
          if (e.key === 'Escape') {
            e.preventDefault()
            e.stopPropagation()
          }
        }}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
            <Clock className="w-5 h-5" />
            You&apos;ve been idle
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            No activity detected for{' '}
            <span className="font-semibold text-foreground">{formatDuration(idleSeconds)}</span>.
            What would you like to do with this time?
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-2.5 mt-2">
          {/* Option 1: Keep Time & Continue */}
          <button
            id="idle-modal-keep-continue"
            type="button"
            onClick={handleKeepAndContinue}
            disabled={isLoading}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 rounded-lg border border-border',
              'bg-card hover:bg-muted/50 transition-colors text-left',
              'disabled:opacity-50 disabled:cursor-not-allowed',
            )}
          >
            <Clock className="w-4 h-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">Keep Time & Continue</p>
              <p className="text-xs text-muted-foreground">
                Resume timer (keep the idle time)
              </p>
            </div>
          </button>

          {/* Option 2: Discard Idle & Stop */}
          <button
            id="idle-modal-discard-stop"
            type="button"
            onClick={handleDiscardAndStop}
            disabled={isLoading}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 rounded-lg border border-border',
              'bg-card hover:bg-muted/50 transition-colors text-left',
              'disabled:opacity-50 disabled:cursor-not-allowed',
            )}
          >
            {pendingAction === 'discard-stop' ? (
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            ) : (
              <Scissors className="w-4 h-4 text-muted-foreground" />
            )}
            <div>
              <p className="text-sm font-medium">Discard Idle & Stop</p>
              <p className="text-xs text-muted-foreground">
                Stop at the moment you went idle (trim{' '}
                <span className="font-medium text-amber-600">{formatDuration(idleSeconds)}</span>)
              </p>
            </div>
          </button>

          {/* Option 3: Discard Idle & Continue */}
          <button
            id="idle-modal-discard-continue"
            type="button"
            onClick={handleDiscardAndContinue}
            disabled={isLoading}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 rounded-lg border border-[#F06900]/40',
              'bg-[#FFF0E6] dark:bg-orange-900/20 hover:bg-[#FFE4CC] dark:hover:bg-orange-900/30',
              'transition-colors text-left',
              'disabled:opacity-50 disabled:cursor-not-allowed',
            )}
          >
            {pendingAction === 'discard-continue' ? (
              <Loader2 className="w-4 h-4 animate-spin text-[#F06900]" />
            ) : (
              <Play className="w-4 h-4 text-[#F06900] fill-[#F06900]" />
            )}
            <div>
              <p className="text-sm font-medium text-[#F06900]">Discard Idle & Continue</p>
              <p className="text-xs text-muted-foreground">Trim idle time, but start a new timer now</p>
            </div>
          </button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
