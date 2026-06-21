import { apiClient } from '@/lib/api-client'

export interface TimesheetSubmission {
  id: string
  workspace_id: string
  user_id: string
  week_start: string // YYYY-MM-DD
  status: 'pending' | 'approved' | 'rejected'
  reviewer_id: string | null
  rejection_note: string | null
  submitted_at: string
  reviewed_at: string | null
}

export interface PendingSubmissionsResponse {
  data: TimesheetSubmission[]
  total: number
  page: number
  per_page: number
}

export interface ListPendingParams {
  workspace_id: string
  user_id?: string
  page?: number
  per_page?: number
}

export const approvalsApi = {
  submitWeek: (workspaceId: string, weekStart: string) =>
    apiClient.post<{ data: TimesheetSubmission }>(
      '/approvals/submit',
      { week_start: weekStart },
      { params: { workspace_id: workspaceId } }
    ),

  listPending: (params: ListPendingParams) =>
    apiClient.get<PendingSubmissionsResponse>('/approvals/pending', { params }),

  approveWeek: (workspaceId: string, submissionId: string) =>
    apiClient.post<{ data: TimesheetSubmission }>(
      `/approvals/${submissionId}/approve`,
      null,
      { params: { workspace_id: workspaceId } }
    ),

  rejectWeek: (workspaceId: string, submissionId: string, note: string) =>
    apiClient.post<{ data: TimesheetSubmission }>(
      `/approvals/${submissionId}/reject`,
      { note },
      { params: { workspace_id: workspaceId } }
    ),
}
