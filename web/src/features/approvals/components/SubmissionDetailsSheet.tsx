import { useState } from 'react'
import { format, addDays } from 'date-fns'
import { useTimeEntries } from '@/features/time-entries/hooks'
import { formatDuration } from '@/lib/utils'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'

interface SubmissionDetailsSheetProps {
  workspaceId: string
  submission: any | null // TimesheetSubmissionResponse
  memberName: string
  isOpen: boolean
  onClose: () => void
}

export function SubmissionDetailsSheet({
  workspaceId,
  submission,
  memberName,
  isOpen,
  onClose,
}: SubmissionDetailsSheetProps) {
  const weekStart = submission?.week_start ? new Date(submission.week_start) : new Date()
  const weekEnd = addDays(weekStart, 6)

  const { data: entriesData, isLoading } = useTimeEntries({
    workspace_id: workspaceId,
    user_id: submission?.user_id,
    limit: 200, // API accepts max 200
    date_from: submission?.week_start,
    date_to: format(weekEnd, 'yyyy-MM-dd'),
  }, {
    enabled: isOpen && !!submission
  })

  // Only consider entries that were actually submitted (pending/approved/rejected)
  // or maybe all entries in that week? Usually, just pending/approved ones.
  const entries = (entriesData?.data ?? []).filter(e => e.status !== 'draft' && e.status !== 'running')

  // Group entries by day
  const groupedEntries = entries.reduce((acc, entry) => {
    const day = format(new Date(entry.start_time), 'yyyy-MM-dd')
    if (!acc[day]) acc[day] = []
    acc[day].push(entry)
    return acc
  }, {} as Record<string, typeof entries>)

  const days = Array.from({ length: 7 }, (_, i) => format(addDays(weekStart, i), 'yyyy-MM-dd'))

  const totalSeconds = entries.reduce((sum, e) => sum + (e.duration_seconds || 0), 0)

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="w-[400px] sm:w-[600px] flex flex-col p-6 overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            Timesheet Details
            <span className="block text-sm font-normal text-muted-foreground mt-1">
              {memberName} • Week of {format(weekStart, 'MMM d, yyyy')}
            </span>
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6 flex-1">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center text-muted-foreground py-10">
              No submitted time entries found for this week.
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex justify-between items-center bg-muted/30 p-3 rounded-lg border border-border">
                <span className="font-medium text-foreground">Total Weekly Time</span>
                <span className="font-mono font-bold text-lg">{formatDuration(totalSeconds)}</span>
              </div>

              {days.map(day => {
                const dayEntries = groupedEntries[day] || []
                if (dayEntries.length === 0) return null

                const dayTotal = dayEntries.reduce((sum, e) => sum + (e.duration_seconds || 0), 0)

                return (
                  <div key={day} className="space-y-3">
                    <div className="flex justify-between items-center border-b border-border pb-1">
                      <h4 className="text-sm font-semibold text-foreground">
                        {format(new Date(day), 'EEEE, MMM d')}
                      </h4>
                      <span className="text-sm font-mono font-medium text-muted-foreground">
                        {formatDuration(dayTotal)}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {dayEntries.map(entry => (
                        <div key={entry.id} className="flex flex-col bg-card border border-border rounded-lg p-3 text-sm">
                          <div className="flex justify-between items-start mb-1.5">
                            <div className="flex items-center gap-2">
                              <span
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: entry.project_color ?? '#ccc' }}
                              />
                              <span className="font-medium">{entry.project_name}</span>
                              {entry.task_name && (
                                <>
                                  <span className="text-muted-foreground text-xs">▶</span>
                                  <span className="text-muted-foreground">{entry.task_name}</span>
                                </>
                              )}
                            </div>
                            <span className="font-mono font-medium">{formatDuration(entry.duration_seconds || 0)}</span>
                          </div>
                          
                          {entry.description ? (
                            <p className="text-muted-foreground mt-0.5">{entry.description}</p>
                          ) : (
                            <p className="text-muted-foreground/50 italic mt-0.5">No description</p>
                          )}
                          
                          {entry.tags && entry.tags.length > 0 && (
                            <div className="flex gap-1.5 mt-2 flex-wrap">
                              {entry.tags.map(tag => (
                                <span key={tag.id} className="text-[10px] uppercase tracking-wider bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                                  {tag.name}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="mt-8 pt-4 border-t border-border">
          <button
            onClick={onClose}
            className="w-full py-2.5 text-sm rounded-lg border border-border hover:bg-muted transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
