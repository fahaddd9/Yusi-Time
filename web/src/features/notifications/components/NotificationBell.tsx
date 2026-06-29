'use client'
/**
 * NotificationBell — Phase 6 (regular) + Phase 6.5 (attendance) types.
 *
 * Addendum §6.7: Two new notification type renderings in the existing
 * Notification Sheet:
 *   - work_start_missed:           "Missed work start" (self, Member)
 *   - flexible_reminder_missed:    "Flexible hours reminder" (self, Member)
 *   - daily_hours_shortfall:       "Daily shortfall — <MemberName>" (Admin/Manager view)
 *
 * Implementation: the two streams (regular `notifications` + attendance
 * `attendance_notifications`) are normalised into a single `UnifiedItem`
 * shape and merged/sorted by `created_at` DESC for a single list. The bell
 * badge count is the sum of both unread counts. No new list mechanism is
 * introduced — both streams use the same card rendering.
 *
 * scope is auto-selected:
 *   - 'self'    → Member (sees only their own attendance notifications)
 *   - 'managed' → Admin/Manager (sees all Members' daily shortfall notifications)
 *
 * The attendance stream is only fetched when the active workspace has
 * attendance_enabled (via useWorkspace). For non-attendance workspaces the
 * bell behaves exactly as before.
 */

import React, { useEffect, useState, useRef, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bell, Check, Clock, FileText, XCircle, CheckCircle2,
  AlarmClock, Timer, TrendingDown, Users,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
} from '../hooks/useNotifications'
import { useAttendanceNotifications } from '@/features/attendance/hooks/useAttendance'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useWorkspace, useWorkspaces } from '@/features/settings/hooks'
import type { AttendanceNotification } from '@/features/attendance/api'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

// ── Unified item shape ────────────────────────────────────────────────────────

type NotificationSource = 'regular' | 'attendance'

interface UnifiedItem {
  id: string
  source: NotificationSource
  eventType: string      // e.g. 'timesheet_approved', 'work_start_missed'
  title: string
  message: string
  isRead: boolean
  createdAt: string
  /** Original IDs needed for mark-read calls */
  regularId?: string
  attendanceId?: string
  metadata?: Record<string, any>
}

// ── Attendance notification copy generator ────────────────────────────────────

function attendanceToUnified(n: AttendanceNotification): UnifiedItem {
  let title = ''
  let message = ''

  switch (n.notification_type) {
    case 'work_start_missed':
      title = 'Missed work start'
      message = n.late_by_minutes != null && n.late_by_minutes > 0
        ? `You were ${formatMinutes(n.late_by_minutes)} late on ${formatDate(n.related_date)}. Did you forget to start tracking?`
        : `You didn't start tracking on time on ${formatDate(n.related_date)}.`
      break
    case 'flexible_reminder_missed':
      title = 'Hours reminder'
      message = `You haven't logged any time on ${formatDate(n.related_date)}. There's still time to reach your daily target.`
      break
    case 'daily_hours_shortfall': {
      const name = n.user_full_name ?? 'A team member'
      const logged = n.hours_logged != null ? n.hours_logged.toFixed(1) : '0.0'
      const target = n.daily_required_hours != null ? n.daily_required_hours.toFixed(1) : '0.0'
      
      title = 'Daily shortfall'
      message = `${name} did not log their required hours on ${formatDate(n.related_date)}. They logged ${logged}h of ${target}h.`
      break
    }
  }

  return {
    id: `att-${n.id}`,
    source: 'attendance',
    eventType: n.notification_type,
    title,
    message,
    isRead: n.is_read,
    createdAt: n.created_at,
    attendanceId: n.id,
  }
}

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

function formatDate(dateStr: string): string {
  // YYYY-MM-DD → "Jun 24"
  try {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

// ── Icon map ──────────────────────────────────────────────────────────────────

function getEventIcon(eventType: string) {
  switch (eventType) {
    // Regular notification types
    case 'timesheet_approved':
      return (
        <div className="p-2 rounded-full bg-emerald-500/10 text-emerald-500">
          <CheckCircle2 className="h-4 w-4" />
        </div>
      )
    case 'timesheet_rejected':
      return (
        <div className="p-2 rounded-full bg-rose-500/10 text-rose-500">
          <XCircle className="h-4 w-4" />
        </div>
      )
    case 'timesheet_submitted':
      return (
        <div className="p-2 rounded-full bg-blue-500/10 text-blue-500">
          <FileText className="h-4 w-4" />
        </div>
      )
    // Phase 6.5 attendance types (Addendum §6.7)
    case 'work_start_missed':
      return (
        <div className="p-2 rounded-full bg-amber-500/10 text-amber-500">
          <AlarmClock className="h-4 w-4" />
        </div>
      )
    case 'flexible_reminder_missed':
      return (
        <div className="p-2 rounded-full bg-[#FE6900]/10 text-[#FE6900]">
          <Timer className="h-4 w-4" />
        </div>
      )
    case 'daily_hours_shortfall':
      return (
        <div className="p-2 rounded-full bg-rose-500/10 text-rose-500">
          <TrendingDown className="h-4 w-4" />
        </div>
      )
    default:
      return (
        <div className="p-2 rounded-full bg-primary/10 text-primary">
          <Bell className="h-4 w-4" />
        </div>
      )
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

export function NotificationBell() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const workspaceId = activeWorkspaceId ?? ''

  // Role for attendance scope
  const { data: workspacesData } = useWorkspaces()
  const activeWs = workspacesData?.find((w: any) => w.id === activeWorkspaceId)
  const role = activeWs?.role ?? 'viewer'

  // Workspace attendance settings
  const { data: workspaceDetail } = useWorkspace(activeWorkspaceId)
  const attendanceEnabled = workspaceDetail?.attendance_enabled ?? false

  // Regular notifications
  const { data: response, isLoading } = useNotifications({ workspace_id: workspaceId })
  const { mutate: markAllRead } = useMarkAllNotificationsRead()
  const { mutate: markRead } = useMarkNotificationRead()

  const regularUnread = response?.unread_count || 0

  // Attendance notifications are always scoped to 'self' for the personal Bell.
  // Admins receive daily_hours_shortfall targeted directly to them.
  const attScope = 'self'
  const { data: attResponse } = useAttendanceNotifications(
    { workspace_id: workspaceId, scope: attScope, per_page: 20 },
    attendanceEnabled
  )
  const attUnread = attResponse?.unread_count ?? 0
  
  const unified = useMemo<UnifiedItem[]>(() => {
    const regularNotifications = response?.data || []
    const attNotifications = attResponse?.data ?? []

    const regularItems: UnifiedItem[] = regularNotifications.map((n) => ({
      id: `reg-${n.id}`,
      source: 'regular' as const,
      eventType: n.event_type,
      title: n.title,
      message: n.message,
      isRead: n.read_at !== null,
      createdAt: n.created_at,
      regularId: n.id,
      metadata: n.event_metadata || undefined,
    }))

    const attItems = attNotifications.map(attendanceToUnified)

    return [...regularItems, ...attItems].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    )
  }, [response?.data, attResponse?.data])

  const totalUnread = regularUnread + attUnread

  const [isOpen, setIsOpen] = useState(false)
  const markAllReadTimer = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (isOpen && totalUnread > 0) {
      markAllReadTimer.current = setTimeout(() => {
        markAllRead(workspaceId)
      }, 2000)
    } else {
      if (markAllReadTimer.current) clearTimeout(markAllReadTimer.current)
    }

    return () => {
      if (markAllReadTimer.current) clearTimeout(markAllReadTimer.current)
    }
  }, [isOpen, totalUnread, workspaceId, markAllRead])

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className="relative text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          >
            <Bell className="h-5 w-5" />
            <AnimatePresence>
              {totalUnread > 0 && (
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  key={totalUnread}
                  transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                  className="absolute top-0 right-0 flex h-4 w-4 items-center justify-center rounded-full bg-[#F06900] text-[9px] font-bold text-white shadow-sm ring-2 ring-background"
                >
                  {totalUnread > 9 ? '9+' : totalUnread}
                </motion.div>
              )}
            </AnimatePresence>
          </Button>
        }
      />

      <SheetContent
        className="w-[380px] sm:w-[450px] p-0 flex flex-col bg-background/95 backdrop-blur-xl"
      >
        <SheetHeader className="p-5 pr-14 border-b border-border/40 space-y-0 flex-row items-center justify-between bg-card/50">
          <SheetTitle className="text-lg font-semibold tracking-tight">
            Notifications
          </SheetTitle>
          {totalUnread > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => markAllRead(workspaceId)}
              className="h-8 text-xs font-medium text-primary hover:text-primary/80 hover:bg-primary/10 transition-colors"
            >
              <Check className="h-3.5 w-3.5 mr-1.5" />
              Mark all as read
            </Button>
          )}
        </SheetHeader>

        <ScrollArea className="flex-1 min-h-0">
          <div className="px-4 py-5">
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-4 p-4 rounded-2xl border border-border/30 bg-card/50">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="space-y-2 flex-1">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : unified.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 mt-20">
                <div className="h-20 w-20 rounded-full bg-primary/5 flex items-center justify-center mb-2">
                  <Bell className="h-10 w-10 text-primary/30" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-foreground">You&apos;re all caught up!</h3>
                  <p className="text-sm text-muted-foreground mt-1 max-w-[200px] mx-auto">
                    When you have new notifications, they will appear here.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {unified.map((item) => (
                  <motion.div
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={item.id}
                    className={cn(
                      'group relative flex gap-4 p-4 rounded-2xl transition-all duration-300 cursor-pointer overflow-hidden border',
                      !item.isRead
                        ? 'bg-card border-primary/20 shadow-md shadow-primary/5 hover:border-primary/40'
                        : 'bg-muted/30 border-transparent hover:bg-card hover:border-border/50 hover:shadow-sm'
                    )}
                    onClick={() => {
                      if (!item.isRead) {
                        const idToMark = item.regularId || item.attendanceId
                        if (idToMark) {
                          markRead([idToMark])
                        }
                      }
                    }}
                  >
                    {/* Unread accent line */}
                    {!item.isRead && (
                      <div
                        className={cn(
                          'absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b',
                          item.source === 'attendance'
                            ? 'from-amber-500 to-orange-400'
                            : 'from-[#F06900] to-orange-400'
                        )}
                      />
                    )}

                    <div className="shrink-0 mt-0.5 relative z-10">
                      {getEventIcon(item.eventType)}
                    </div>

                    <div className="flex-1 min-w-0 relative z-10">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <p
                          className={cn(
                            'text-sm tracking-tight',
                            !item.isRead ? 'font-semibold text-foreground' : 'font-medium text-foreground/80'
                          )}
                        >
                          {item.title}
                        </p>
                        <span className="text-[10px] whitespace-nowrap text-muted-foreground/80 font-medium flex items-center shrink-0 mt-0.5">
                          {formatDistanceToNow(new Date(item.createdAt), { addSuffix: true }).replace('about ', '')}
                        </span>
                      </div>
                      <p
                        className={cn(
                          'text-xs leading-relaxed line-clamp-2',
                          !item.isRead ? 'text-muted-foreground/90' : 'text-muted-foreground/70'
                        )}
                      >
                        {item.message}
                      </p>
                      {item.metadata?.note && (
                        <div className="mt-2 text-xs p-2 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400">
                          <span className="font-semibold block mb-0.5">Rejection Note:</span>
                          {item.metadata.note}
                        </div>
                      )}
                      {/* Attendance source badge */}
                      {item.source === 'attendance' && (
                        <span className="inline-flex items-center gap-1 mt-1.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border border-amber-200/50 dark:border-amber-800/50">
                          <Clock className="w-2.5 h-2.5" />
                          Attendance
                        </span>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
