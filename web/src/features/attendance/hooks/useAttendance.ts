/**
 * Attendance hooks — Phase 6.5, Addendum §4.1, §4.2, §4.4.
 *
 * Hooks:
 *   useAttendanceSettings      — read/update attendance config (Admin)
 *   useBillableSettings        — read/update billable toggle (Admin)
 *   useDailyProgress           — F2 Timer Bar badge data, polls every 30s (Member)
 *   useWorkStartResponse       — F1 "start"/"not_now" mutation (Member)
 *   useAttendanceNotifications — paginated attendance notification list
 *   usePushSubscription        — register/unregister browser push subscription
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  attendanceApi,
  AttendanceSettings,
  BillableSettings,
  DailyProgress,
  WorkStartResponsePayload,
  ListAttendanceNotificationsParams,
  UpdateAttendanceSettingsParams,
} from '../api'

// ── Query key factory (mirrors notificationKeys pattern) ──────────────────────

export const attendanceKeys = {
  all: ['attendance'] as const,
  settings: (workspaceId: string) =>
    [...attendanceKeys.all, 'settings', workspaceId] as const,
  billable: (workspaceId: string) =>
    [...attendanceKeys.all, 'billable', workspaceId] as const,
  dailyProgress: (workspaceId: string) =>
    [...attendanceKeys.all, 'daily-progress', workspaceId] as const,
  notifications: (params: ListAttendanceNotificationsParams) =>
    [...attendanceKeys.all, 'notifications', params] as const,
}

// ── useAttendanceSettings ─────────────────────────────────────────────────────

/**
 * Query + mutation pair for workspace attendance configuration.
 * Admin only (enforcement at API layer). Addendum §4.1.
 *
 * Note: there is no dedicated GET /attendance-settings endpoint — settings
 * are read from the workspace detail response. This hook provides only
 * the PATCH mutation; the current settings come from useWorkspace().
 */
export function useUpdateAttendanceSettings(workspaceId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (params: Omit<UpdateAttendanceSettingsParams, 'workspace_id'>) =>
      attendanceApi.updateAttendanceSettings({ workspace_id: workspaceId, ...params }),

    onSuccess: () => {
      // Invalidate workspace queries so updated settings surface everywhere
      queryClient.invalidateQueries({ queryKey: ['workspaces', workspaceId] })
      queryClient.invalidateQueries({ queryKey: attendanceKeys.settings(workspaceId) })
    },
  })
}

// ── useBillableSettings ────────────────────────────────────────────────────────

/**
 * Mutation to toggle workspace billable tracking.
 * Admin only. Addendum §4.1, PRD-ADD-05, PRD-ADD-06.
 */
export function useUpdateBillableSettings(workspaceId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (is_billable: boolean) =>
      attendanceApi.updateBillableSettings(workspaceId, is_billable),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces', workspaceId] })
      queryClient.invalidateQueries({ queryKey: attendanceKeys.billable(workspaceId) })
    },
  })
}

// ── useDailyProgress ─────────────────────────────────────────────────────────

/**
 * F2 — Polls the daily-progress endpoint every 30s.
 * Member only (PRD-ADD-03 — enforced at API; Admin gets 403).
 * Addendum §4.2, §6.4.
 *
 * enabled: pass false when workspace_id is unavailable or user is Admin/Manager.
 *
 * Returns null-safe data: when daily_required_hours is null, the Timer Bar
 * badge should NOT be rendered (Addendum §4.5).
 */
export function useDailyProgress(workspaceId: string, enabled = true) {
  return useQuery({
    queryKey: attendanceKeys.dailyProgress(workspaceId),
    queryFn: async () => {
      const res = await attendanceApi.getDailyProgress(workspaceId)
      return res.data as DailyProgress
    },
    enabled: !!workspaceId && enabled,
    // Poll every 30s for live updates (Addendum §4.5 polling interval)
    refetchInterval: 30_000,
    staleTime: 25_000,
    // Don't throw on 403 — silently return null so non-Member roles see nothing
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 403) return false
      return failureCount < 2
    },
  })
}

// ── useWorkStartResponse ──────────────────────────────────────────────────────

/**
 * F1 — Mutation for Member's response to the work-start prompt modal.
 * Addendum §4.2, §2.2.
 *
 * 'not_now': dismisses the prompt, creates attendance_notification record.
 * 'start': creates a timer entry and returns time_entry_id.
 *
 * onSuccess invalidates timer queries (so running timer UI updates) and
 * daily-progress (so Timer Bar reflects the new entry immediately).
 */
export function useWorkStartResponse(workspaceId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: WorkStartResponsePayload) =>
      attendanceApi.postWorkStartResponse(workspaceId, payload),

    onSuccess: (_, variables) => {
      // If a timer was started, invalidate current-timer query
      if (variables.response === 'start') {
        queryClient.invalidateQueries({ queryKey: ['currentTimer', workspaceId] })
        queryClient.invalidateQueries({ queryKey: ['time-entries'] })
      }
      // Always refresh daily progress so badge updates
      queryClient.invalidateQueries({
        queryKey: attendanceKeys.dailyProgress(workspaceId),
      })
    },
  })
}

// ── useAttendanceNotifications ────────────────────────────────────────────────

/**
 * Paginated attendance notifications with 30s polling.
 * Addendum §4.4.
 *
 * scope='self' (default): only notifications where recipient=caller.
 * scope='managed': all workspace attendance notifications (Admin/Manager only).
 */
export function useAttendanceNotifications(
  params: ListAttendanceNotificationsParams,
  enabled = true
) {
  return useQuery({
    queryKey: attendanceKeys.notifications(params),
    queryFn: async () => {
      const res = await attendanceApi.listAttendanceNotifications(params)
      return res.data
    },
    enabled: !!params.workspace_id && enabled,
    refetchInterval: 30_000,
    staleTime: 25_000,
    // Silently suppress 403 (Member requesting managed scope)
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 403) return false
      return failureCount < 2
    },
  })
}

// ── usePushSubscription ───────────────────────────────────────────────────────

/**
 * Mutation pair for Web Push subscription management.
 * Addendum §4.3, §6.8.
 *
 * IMPORTANT — Addendum §6.8 browser permission rule:
 *   registerPushSubscription MUST only be called as a result of a direct
 *   user gesture (e.g. button click). Never call on page load automatically.
 *   The browser enforces this — calling Notification.requestPermission()
 *   without a user gesture will be silently ignored or throw.
 */
export function usePushSubscription() {
  return {
    register: useMutation({
      mutationFn: (payload: {
        endpoint: string
        p256dh_key: string
        auth_key: string
      }) => attendanceApi.registerPushSubscription(payload),
    }),
    unregister: useMutation({
      mutationFn: (subscriptionId: string) =>
        attendanceApi.deletePushSubscription(subscriptionId),
    }),
  }
}
