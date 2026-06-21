'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { Check, X, Eye, FileText } from 'lucide-react'
import { usePendingApprovals, useApproveWeek, useRejectWeek } from '../hooks/useApprovals'
import { useWorkspaceMembers } from '@/features/settings/hooks'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
import { Textarea } from '@/components/ui/textarea'

import { SubmissionDetailsSheet } from './SubmissionDetailsSheet'

interface ApprovalListProps {
  workspaceId: string
}

export function ApprovalList({ workspaceId }: ApprovalListProps) {
  const { data: response, isLoading } = usePendingApprovals({ workspace_id: workspaceId })
  const { data: membersResponse } = useWorkspaceMembers(workspaceId)
  
  const approveWeek = useApproveWeek()
  const rejectWeek = useRejectWeek()

  const pendingList = response?.data || []
  const members = membersResponse?.items || []

  const [rejectDialog, setRejectDialog] = useState<{ isOpen: boolean; submissionId: string | null }>({
    isOpen: false,
    submissionId: null,
  })
  const [rejectNote, setRejectNote] = useState('')

  const [approveDialog, setApproveDialog] = useState<{ isOpen: boolean; submissionId: string | null }>({
    isOpen: false,
    submissionId: null,
  })

  const [viewSheet, setViewSheet] = useState<{ isOpen: boolean; submission: any | null; memberName: string }>({
    isOpen: false,
    submission: null,
    memberName: '',
  })

  const handleApprove = async () => {
    if (!approveDialog.submissionId) return
    await approveWeek.mutateAsync({ workspaceId, submissionId: approveDialog.submissionId })
    setApproveDialog({ isOpen: false, submissionId: null })
  }

  const handleReject = async () => {
    if (!rejectDialog.submissionId || !rejectNote.trim()) return
    await rejectWeek.mutateAsync({
      workspaceId,
      submissionId: rejectDialog.submissionId,
      note: rejectNote.trim(),
    })
    setRejectDialog({ isOpen: false, submissionId: null })
    setRejectNote('')
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  if (pendingList.length === 0) {
    return (
      <div className="border border-dashed rounded-xl p-12 text-center text-muted-foreground bg-muted/10">
        <FileText className="h-10 w-10 mx-auto mb-3 opacity-20" />
        <p className="text-base font-medium text-foreground">All caught up!</p>
        <p className="text-sm mt-1">There are no pending timesheets to review.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Team Member</th>
              <th className="px-4 py-3 font-medium">Week Of</th>
              <th className="px-4 py-3 font-medium">Submitted</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {pendingList.map((sub) => {
              const member = members.find((m) => m.user_id === sub.user_id)
              const memberName = member?.full_name || 'Unknown User'
              
              return (
                <tr key={sub.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3 font-medium">
                    {memberName}
                  </td>
                  <td className="px-4 py-3">
                    {format(new Date(sub.week_start), 'MMM d, yyyy')}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {format(new Date(sub.submitted_at), 'MMM d, h:mm a')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground hover:text-foreground"
                        onClick={() => setViewSheet({ isOpen: true, submission: sub, memberName })}
                      >
                        <Eye className="h-4 w-4 mr-1.5" />
                        View
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={approveWeek.isPending || rejectWeek.isPending}
                        className="text-[hsl(var(--status-approved))] hover:text-[hsl(var(--status-approved))] hover:bg-[hsl(var(--status-approved-muted))]"
                        onClick={() => setApproveDialog({ isOpen: true, submissionId: sub.id })}
                      >
                        <Check className="h-4 w-4 mr-1.5" />
                        Approve
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={approveWeek.isPending || rejectWeek.isPending}
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => setRejectDialog({ isOpen: true, submissionId: sub.id })}
                      >
                        <X className="h-4 w-4 mr-1.5" />
                        Reject
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <SubmissionDetailsSheet 
        workspaceId={workspaceId}
        submission={viewSheet.submission}
        memberName={viewSheet.memberName}
        isOpen={viewSheet.isOpen}
        onClose={() => setViewSheet(prev => ({ ...prev, isOpen: false }))}
      />

      <Dialog
        open={rejectDialog.isOpen}
        onOpenChange={(open) => {
          if (!open) {
            setRejectDialog({ isOpen: false, submissionId: null })
            setRejectNote('')
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Timesheet</DialogTitle>
            <DialogDescription>
              Please provide a reason for rejecting this timesheet. This note will be sent to the team member.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-2">
            <Textarea
              placeholder="e.g., Missing project descriptions for Tuesday..."
              value={rejectNote}
              onChange={(e) => setRejectNote(e.target.value)}
              className={`min-h-[100px] focus-visible:ring-[#F06900] ${rejectNote.length > 1000 ? 'border-destructive focus-visible:ring-destructive' : ''}`}
              maxLength={1000}
            />
            <div className="flex justify-between items-center text-xs">
              {!rejectNote.trim() ? (
                <span className="text-destructive font-medium">Rejection note is required</span>
              ) : <span></span>}
              <span className={`${rejectNote.length >= 900 ? 'text-destructive font-bold' : 'text-muted-foreground'}`}>
                {rejectNote.length} / 1000
              </span>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRejectDialog({ isOpen: false, submissionId: null })}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={!rejectNote.trim() || rejectWeek.isPending}
            >
              {rejectWeek.isPending ? 'Rejecting...' : 'Reject Timesheet'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <AlertDialog
        open={approveDialog.isOpen}
        onOpenChange={(open) => {
          if (!open) setApproveDialog({ isOpen: false, submissionId: null })
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Approve Timesheet</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to approve this timesheet? The team member will be notified.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={(e) => {
                e.preventDefault()
                handleApprove()
              }} 
              disabled={approveWeek.isPending}
              className="bg-[hsl(var(--status-approved))] text-white hover:bg-[hsl(var(--status-approved))]/90"
            >
              {approveWeek.isPending ? 'Approving...' : 'Approve'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
