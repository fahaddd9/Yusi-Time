/**
 * useWorkStartTrigger — Phase 6.5, Addendum §6.1.
 *
 * Polls the attendance notifications endpoint every 30s looking for
 * unread work_start_missed / flexible_reminder_missed notifications
 * from today. When one is found (and no modal is already open), opens
 * the WorkStartModal via the attendance store.
 *
 * PRD-ADD-03: Only runs for Member role. Suppressed silently for
 * Admin/Manager (403 from daily-progress endpoint is caught by the
 * retry:false logic in useDailyProgress — same pattern here).
 *
 * Called from (app)/layout.tsx. Mounts exactly once per session.
 * The polling interval matches the backend scheduler interval (30s)
 * so the modal appears within ~30 seconds of the notification being
 * created server-side.
 *
 * Late-arrival handling:
 *   If the Member opens the app AFTER work_start_time has already passed
 *   (and has not yet been prompted), the backend creates a notification
 *   immediately when the scheduler next runs. This hook picks it up and
 *   opens the modal with the late_by_minutes value already stored in the
 *   notification record.
 */

import { useEffect, useRef } from 'react'
import { useAttendanceNotifications } from './useAttendance'
import { useAttendanceStore } from '@/stores/attendance-store'

interface WorkStartTriggerOptions {
  workspaceId: string
  /** User's role in the active workspace. Admin/Manager = suppressed. */
  role: string
  /** attendance_mode from workspace settings ('fixed_schedule' | 'flexible_hours') */
  attendanceMode: 'fixed_schedule' | 'flexible_hours'
  /** Whether attendance is enabled in the workspace. False = suppressed. */
  attendanceEnabled: boolean
  /** Time of day when work starts in "HH:MM:SS" format */
  workStartTime?: string | null
}

export function useWorkStartTrigger({
  workspaceId,
  role,
  attendanceMode,
  attendanceEnabled,
  workStartTime,
}: WorkStartTriggerOptions) {
  const { workStartOpen, openWorkStart } = useAttendanceStore()

  // Only poll for Member role when attendance is enabled (PRD-ADD-03)
  const enabled = role === 'member' && attendanceEnabled && !!workspaceId

  const { data: notificationsData } = useAttendanceNotifications(
    { workspace_id: workspaceId, scope: 'self', per_page: 5 },
    enabled
  )

  // Track which notification IDs we've already acted on to prevent re-open
  const shownNotificationIds = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!enabled || workStartOpen || !notificationsData) return

    const d = new Date()
    const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

    // Look for an unread work-start notification from today that we haven't shown yet
    const trigger = notificationsData.data.find(
      (n) =>
        !n.is_read &&
        n.related_date === today &&
        (n.notification_type === 'work_start_missed' ||
          n.notification_type === 'flexible_reminder_missed') &&
        !shownNotificationIds.current.has(n.id)
    )

    // DEBUG: Alert the user to what we found
    console.log(`[DEBUG] Polled! found: ${notificationsData.data.length} notifs. trigger: ${trigger ? 'YES' : 'NO'}`)

    if (!trigger) return

    // Mark as shown so we don't re-open if modal is closed and data re-fetches
    shownNotificationIds.current.add(trigger.id)

    let lateByMinutes = trigger.late_by_minutes

    // Dynamically calculate lateness if it's fixed schedule and we have a start time
    if (attendanceMode === 'fixed_schedule' && workStartTime) {
      const now = new Date()
      const [h, m, s] = workStartTime.split(':').map(Number)
      
      const targetTime = new Date(now)
      targetTime.setHours(h, m, s || 0, 0)

      const diffMs = now.getTime() - targetTime.getTime()
      if (diffMs > 0) {
        const diffMins = Math.floor(diffMs / 60000)
        // Only override if the dynamic lateness is larger (or the backend value was null)
        if (lateByMinutes === null || diffMins > lateByMinutes) {
          lateByMinutes = diffMins
        }
      }
    }

    openWorkStart({
      workspace_id: workspaceId,
      attendance_mode: attendanceMode,
      late_by_minutes: lateByMinutes,
    })
  }, [notificationsData, workStartOpen, enabled, workspaceId, attendanceMode, workStartTime, openWorkStart])

  // Local exact-time trigger for Fixed Schedule
  useEffect(() => {
    if (!enabled || workStartOpen || attendanceMode !== 'fixed_schedule' || !workStartTime) return

    const now = new Date()
    const [h, m, s] = workStartTime.split(':').map(Number)
    const targetTime = new Date(now)
    targetTime.setHours(h, m, s || 0, 0)

    const diffMs = targetTime.getTime() - now.getTime()
    
    // If the time is in the future today, set a timeout to trigger it exactly then
    if (diffMs > 0 && diffMs < 24 * 60 * 60 * 1000) {
      console.log(`[DEBUG] Setting local trigger for work_start in ${diffMs}ms`)
      const timerId = setTimeout(() => {
        if (!useAttendanceStore.getState().workStartOpen) {
          openWorkStart({
            workspace_id: workspaceId,
            attendance_mode: attendanceMode,
            late_by_minutes: 0,
          })
        }
      }, diffMs)
      
      return () => clearTimeout(timerId)
    }
  }, [enabled, workStartOpen, attendanceMode, workStartTime, workspaceId, openWorkStart])
}
