/**
 * Time Entry API functions — API Spec v1.1 §12.
 * All 9 endpoints typed and exported.
 */
import { apiClient } from '@/lib/api-client'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TagInEntry {
  id: string
  workspace_id: string
  name: string
  color: string | null
}

export interface TimeEntry {
  id: string
  workspace_id: string
  user_id: string
  user_name: string
  project_id: string
  project_name: string
  project_color: string | null
  task_id: string | null
  task_name: string | null
  description: string | null
  billable: boolean
  status: 'draft' | 'running' | 'pending' | 'approved'
  start_time: string
  end_time: string | null
  duration_seconds: number | null
  tags: TagInEntry[]
  hourly_rate: string | null   // absent for Viewer (API Spec §1.11)
  billable_amount: string | null
  created_at: string
  updated_at: string
}

export interface RoundingResult {
  raw_seconds: number
  rounded_seconds: number
  rounding_mode: string
  rounding_interval_minutes: number | null
}

export interface StartTimerPayload {
  project_id: string
  task_id?: string | null
  description?: string | null
  billable?: boolean | null
  tag_ids?: string[]
  force?: boolean
}

export interface StopTimerPayload {
  idle_end_time?: string | null
}

export interface CreateManualEntryPayload {
  project_id: string
  task_id?: string | null
  start_time: string
  end_time: string
  description?: string | null
  billable?: boolean | null
  tag_ids?: string[]
}

export interface UpdateEntryPayload {
  project_id?: string | null
  task_id?: string | null
  start_time?: string | null
  end_time?: string | null
  description?: string | null
  billable?: boolean | null
  tag_ids?: string[] | null
}

export interface ListEntriesParams {
  workspace_id: string
  cursor?: string | null
  limit?: number
  user_id?: string | null
  project_id?: string | null
  status?: string | null
  billable?: boolean | null
  date_from?: string | null
  date_to?: string | null
  tag_ids?: string | null
}

// ─── API Functions ────────────────────────────────────────────────────────────

export const timeEntriesApi = {
  /** GET /time-entries/current */
  getCurrent: (workspaceId: string) =>
    apiClient.get<{ data: TimeEntry | null }>('/time-entries/current', {
      params: { workspace_id: workspaceId },
    }),

  /** POST /time-entries/start */
  startTimer: (workspaceId: string, payload: StartTimerPayload) =>
    apiClient.post<{ data: TimeEntry }>('/time-entries/start', payload, {
      params: { workspace_id: workspaceId },
    }),

  /** POST /time-entries/{id}/stop */
  stopTimer: (
    workspaceId: string,
    entryId: string,
    payload: StopTimerPayload = {},
  ) =>
    apiClient.post<{ data: TimeEntry; rounding: RoundingResult }>(
      `/time-entries/${entryId}/stop`,
      payload,
      { params: { workspace_id: workspaceId } },
    ),

  /** GET /time-entries */
  listEntries: (params: ListEntriesParams) =>
    apiClient.get<{ data: TimeEntry[]; next_cursor: string | null; limit: number }>(
      '/time-entries',
      { params },
    ),

  /** POST /time-entries (manual) */
  createEntry: (workspaceId: string, payload: CreateManualEntryPayload) =>
    apiClient.post<{ data: TimeEntry; rounding: RoundingResult; has_overlap: boolean }>(
      '/time-entries',
      payload,
      { params: { workspace_id: workspaceId } },
    ),

  /** GET /time-entries/{id} */
  getEntry: (workspaceId: string, entryId: string) =>
    apiClient.get<{ data: TimeEntry }>(`/time-entries/${entryId}`, {
      params: { workspace_id: workspaceId },
    }),

  /** PATCH /time-entries/{id} */
  updateEntry: (workspaceId: string, entryId: string, payload: UpdateEntryPayload) =>
    apiClient.patch<{ data: TimeEntry; rounding: RoundingResult }>(
      `/time-entries/${entryId}`,
      payload,
      { params: { workspace_id: workspaceId } },
    ),

  /** DELETE /time-entries/{id} */
  deleteEntry: (workspaceId: string, entryId: string) =>
    apiClient.delete<{ message: string }>(`/time-entries/${entryId}`, {
      params: { workspace_id: workspaceId },
    }),

  /** POST /time-entries/submit — bulk submit drafts to pending */
  submitEntries: (workspaceId: string, entryIds: string[]) =>
    apiClient.post<{ submitted: string[]; count: number }>(
      '/time-entries/submit',
      { entry_ids: entryIds },
      { params: { workspace_id: workspaceId } },
    ),

  /** POST /time-entries/{id}/continue */
  continue: (entryId: string, params: { workspaceId: string; force?: boolean }) =>
    apiClient.post<{ data: TimeEntry }>(
      `/time-entries/${entryId}/continue`,
      { force: params.force || false },
      { params: { workspace_id: params.workspaceId } },
    ),

  /** POST /time-entries/{id}/duplicate */
  duplicate: (entryId: string, params: { workspaceId: string }) =>
    apiClient.post<{ data: TimeEntry; rounding: RoundingResult }>(
      `/time-entries/${entryId}/duplicate`,
      {},
      { params: { workspace_id: params.workspaceId } },
    ),
}
