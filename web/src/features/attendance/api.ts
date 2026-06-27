/**
 * Attendance API layer — Phase 6.5, Addendum §4.1, §4.2, §4.3, §4.4.
 *
 * Wraps all Phase 6.5 backend endpoints:
 *   PATCH /workspaces/{id}/attendance-settings   → updateAttendanceSettings
 *   PATCH /workspaces/{id}/billable-settings     → updateBillableSettings
 *   GET   /time-entries/daily-progress           → getDailyProgress
 *   POST  /time-entries/work-start-response      → postWorkStartResponse
 *   GET   /notifications/attendance              → listAttendanceNotifications
 *   POST  /users/me/push-subscriptions           → registerPushSubscription
 *   DELETE /users/me/push-subscriptions/{id}    → deletePushSubscription
 */

import { apiClient } from '@/lib/api-client'

// ── Shared types ──────────────────────────────────────────────────────────────

/** Addendum §4.1 attendance settings (workspace-level). */
export interface AttendanceSettings {
  id: string
  attendance_enabled: boolean
  attendance_mode: 'fixed_schedule' | 'flexible_hours'
  /** HH:MM:SS string from API (TIME column) or null */
  work_start_time: string | null
  daily_required_hours: number | null
  /** 0=Sunday, 1=Monday … 6=Saturday */
  off_days: number[]
}

/** Addendum §4.1 billable settings. */
export interface BillableSettings {
  id: string
  is_billable: boolean
}

/**
 * Addendum §4.2 daily progress for Timer Bar badge (Option B pacing).
 * Frontend renders the badge only when daily_required_hours != null.
 */
export interface DailyProgress {
  hours_logged_today: number
  daily_required_hours: number | null
  on_pace: boolean
}

/** Addendum §4.2 work-start-response payload. */
export interface WorkStartResponsePayload {
  response: 'start' | 'not_now'
  project_id?: string
  task_id?: string
}

/** Addendum §4.2 work-start-response result. */
export interface WorkStartResult {
  acknowledged: boolean
  time_entry_id: string | null
  message: string
}

/** Addendum §4.4 single attendance notification. */
export interface AttendanceNotification {
  id: string
  workspace_id: string
  user_id: string
  notification_type:
    | 'work_start_missed'
    | 'flexible_reminder_missed'
    | 'daily_hours_shortfall'
  recipient_user_id: string
  related_date: string // YYYY-MM-DD
  late_by_minutes: number | null
  hours_logged: number | null
  user_full_name: string | null
  daily_required_hours: number | null
  is_read: boolean
  created_at: string
}

/** Addendum §4.4 paginated attendance notifications list. */
export interface AttendanceNotificationsResponse {
  data: AttendanceNotification[]
  total: number
  unread_count: number
  page: number
  per_page: number
}

/** Addendum §4.3 push subscription record. */
export interface PushSubscription {
  id: string
  user_id: string
  endpoint: string
  created_at: string
}

// ── Params types ───────────────────────────────────────────────────────────────

export interface UpdateAttendanceSettingsParams {
  workspace_id: string
  attendance_enabled?: boolean
  attendance_mode?: 'fixed_schedule' | 'flexible_hours'
  /** HH:MM 24h string */
  work_start_time?: string
  daily_required_hours?: number
  off_days?: number[]
}

export interface ListAttendanceNotificationsParams {
  workspace_id: string
  scope?: 'self' | 'managed'
  page?: number
  per_page?: number
}

// ── API object ─────────────────────────────────────────────────────────────────

export const attendanceApi = {
  /**
   * PATCH /workspaces/{id}/attendance-settings
   * Admin only. Addendum §4.1.
   */
  updateAttendanceSettings: ({ workspace_id, ...body }: UpdateAttendanceSettingsParams) =>
    apiClient.patch<AttendanceSettings>(
      `/workspaces/${workspace_id}/attendance-settings`,
      body
    ),

  /**
   * PATCH /workspaces/{id}/billable-settings
   * Admin only. Addendum §4.1, PRD-ADD-05.
   */
  updateBillableSettings: (workspace_id: string, is_billable: boolean) =>
    apiClient.patch<BillableSettings>(
      `/workspaces/${workspace_id}/billable-settings`,
      { is_billable }
    ),

  /**
   * GET /time-entries/daily-progress
   * Member only. Addendum §4.2, §6.4.
   * Poll every 30s for Timer Bar badge.
   */
  getDailyProgress: (workspace_id: string) =>
    apiClient.get<DailyProgress>('/time-entries/daily-progress', {
      params: { workspace_id },
    }),

  /**
   * POST /time-entries/work-start-response
   * Member only. Addendum §4.2.
   * 'start' requires project_id; 'not_now' dismisses.
   */
  postWorkStartResponse: (workspace_id: string, body: WorkStartResponsePayload) =>
    apiClient.post<WorkStartResult>('/time-entries/work-start-response', body, {
      params: { workspace_id },
    }),

  /**
   * GET /notifications/attendance
   * All members. Addendum §4.4.
   * scope='self' (default) or 'managed' (Admin/Manager).
   */
  listAttendanceNotifications: (params: ListAttendanceNotificationsParams) =>
    apiClient.get<AttendanceNotificationsResponse>('/notifications/attendance', {
      params,
    }),

  /**
   * POST /users/me/push-subscriptions
   * Upsert. Addendum §4.3.
   */
  registerPushSubscription: (payload: {
    endpoint: string
    p256dh_key: string
    auth_key: string
  }) =>
    apiClient.post<PushSubscription>('/users/me/push-subscriptions', payload),

  /**
   * DELETE /users/me/push-subscriptions/{id}
   * Addendum §4.3.
   */
  deletePushSubscription: (subscriptionId: string) =>
    apiClient.delete(`/users/me/push-subscriptions/${subscriptionId}`),
}
