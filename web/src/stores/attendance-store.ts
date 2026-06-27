/**
 * Attendance store — Phase 6.5, Addendum §6.1.
 *
 * Tracks the F1 work-start modal state:
 *   - Whether the modal is open
 *   - The workspace context when it opened (mode, late_by_minutes, workspace_id)
 *
 * The modal is opened by the WorkStartTrigger hook (see useWorkStartTrigger)
 * which polls the backend's attendance notifications and shows the modal when
 * an unread work_start_missed / flexible_reminder_missed notification appears.
 *
 * PRD-ADD-03: Only fires for Member role. Admin/Manager state is never set.
 */

import { create } from 'zustand'

export interface WorkStartContext {
  workspace_id: string
  attendance_mode: 'fixed_schedule' | 'flexible_hours'
  /** Minutes past work_start_time. Fixed Schedule mode only. Null in Flexible mode. */
  late_by_minutes: number | null
}

interface AttendanceStore {
  workStartOpen: boolean
  workStartContext: WorkStartContext | null
  openWorkStart: (ctx: WorkStartContext) => void
  closeWorkStart: () => void
  // F2 — Log Out confirmation guard
  logoutGuardOpen: boolean
  logoutGuardHours: { logged: number; required: number } | null
  pendingLogout: (() => void) | null
  openLogoutGuard: (hours: { logged: number; required: number }, onConfirm: () => void) => void
  closeLogoutGuard: () => void
}

export const useAttendanceStore = create<AttendanceStore>((set) => ({
  workStartOpen: false,
  workStartContext: null,
  openWorkStart: (ctx) => set({ workStartOpen: true, workStartContext: ctx }),
  closeWorkStart: () => set({ workStartOpen: false, workStartContext: null }),
  // Logout guard
  logoutGuardOpen: false,
  logoutGuardHours: null,
  pendingLogout: null,
  openLogoutGuard: (hours, onConfirm) =>
    set({ logoutGuardOpen: true, logoutGuardHours: hours, pendingLogout: onConfirm }),
  closeLogoutGuard: () =>
    set({ logoutGuardOpen: false, logoutGuardHours: null, pendingLogout: null }),
}))
