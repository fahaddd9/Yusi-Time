'use client'

import { useState } from 'react'
import { Send } from 'lucide-react'
import { useSubmitWeek } from '@/features/approvals/hooks/useApprovals'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { toast } from 'sonner'
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

interface SubmitWeekButtonProps {
  weekStart: string // YYYY-MM-DD
  draftCount: number
  hasWorkflowEnabled: boolean
}

export function SubmitWeekButton({ weekStart, draftCount, hasWorkflowEnabled }: SubmitWeekButtonProps) {
  const { activeWorkspaceId } = useWorkspaceStore()
  const workspaceId = activeWorkspaceId ?? ''
  const submitWeek = useSubmitWeek()
  const [isOpen, setIsOpen] = useState(false)

  if (!hasWorkflowEnabled) return null

  const canSubmit = draftCount > 0

  const handleConfirm = async () => {
    if (!canSubmit) return
    try {
      await submitWeek.mutateAsync({ workspaceId, weekStart })
      setIsOpen(false)
      toast.success('Timesheet submitted successfully')
    } catch (error: any) {
      if (error.response?.status === 409) {
        toast.error('Timesheet already submitted for this week')
        setIsOpen(false)
      } else {
        toast.error('Failed to submit timesheet')
      }
    }
  }

  return (
    <>
      <button
        id="submit-week-button"
        disabled={!canSubmit || submitWeek.isPending}
        onClick={() => canSubmit && setIsOpen(true)}
        title={!canSubmit ? 'No draft entries to submit' : `Submit ${draftCount} draft ${draftCount === 1 ? 'entry' : 'entries'}`}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
          canSubmit
            ? 'bg-[hsl(var(--status-pending))] text-white hover:opacity-90'
            : 'bg-muted text-muted-foreground cursor-not-allowed opacity-50',
        )}
      >
        <Send className="w-3.5 h-3.5" />
        {submitWeek.isPending ? 'Submitting...' : 'Submit Week'}
        {canSubmit && !submitWeek.isPending && (
          <span className="ml-1 bg-white/20 text-white rounded-full px-1.5 py-0.5 text-[10px] font-bold">
            {draftCount}
          </span>
        )}
      </button>

      <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit Timesheet</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to submit your timesheet for approval? 
              <br /><br />
              <strong>Warning:</strong> Submitted time cannot be edited while pending review.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-[hsl(var(--status-pending))] text-white hover:opacity-90"
              onClick={(e) => {
                e.preventDefault()
                handleConfirm()
              }}
              disabled={submitWeek.isPending}
            >
              {submitWeek.isPending ? 'Submitting...' : 'Submit for Approval'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
