import { apiClient } from '@/lib/api-client'

export interface SummaryReportParams {
  workspace_id: string
  group_by: 'project' | 'user' | 'client' | 'tag'
  date_from: string // YYYY-MM-DD
  date_to: string // YYYY-MM-DD
  project_id?: string
  client_id?: string
  user_id?: string
  billable?: boolean
  status?: string
}

export interface DetailedReportParams {
  workspace_id: string
  date_from: string
  date_to: string
  project_id?: string
  client_id?: string
  task_id?: string
  user_id?: string
  billable?: boolean
  status?: string
  tag_ids?: string[]
  cursor?: string
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface WeeklyReportParams {
  workspace_id: string
  date_from: string
  date_to: string
  user_id?: string
  project_id?: string
  billable?: boolean
}

// Responses
export interface SummaryRow {
  group_key: string | null
  group_label: string | null
  total_seconds: number
  total_hours: number
  non_billable_hours: number
  entry_count: number
  // Financial fields (optional due to suppression layers PRD-ADD-05 / RULE U-01)
  billable_seconds?: number
  billable_hours?: number
  total_billable_amount?: string | null
}

export interface SummaryTotal {
  total_hours: number
  date_from: string
  date_to: string
  total_billable_amount?: string | null
}

export interface SummaryReportResponse {
  data: SummaryRow[]
  summary: SummaryTotal
  // We can include `suppress` if backend returns it, though it's popped by backend router currently.
}

export interface TagRef {
  id: string
  name: string
}

export interface DetailedEntry {
  id: string
  user_id: string
  user_name: string
  project_id: string
  project_name: string | null
  client_id: string | null
  client_name: string | null
  task_id: string | null
  task_name: string | null
  description: string | null
  billable: boolean
  status: string
  start_time: string
  end_time: string | null
  duration_seconds: number | null
  tags: TagRef[]
  // Financial fields (optional due to suppression)
  hourly_rate_cents?: number | null
  billable_amount_cents?: number | null
}

export interface DetailedSummary {
  total_hours: number
  total_billable_amount?: string | null
}

export interface DetailedReportResponse {
  data: DetailedEntry[]
  next_cursor: string | null
  limit: number
  summary: DetailedSummary
}

export interface WeeklyDayCell {
  total_seconds: number
  total_hours: number
  entry_count: number
  billable_hours?: number
  billable_amount?: string | null
}

export interface WeeklyUserRow {
  user_id: string
  user_name: string
  avatar_url: string | null
  total_seconds: number
  total_hours: number
  billable_hours?: number
  total_billable_amount?: string | null
  days: Record<string, WeeklyDayCell> // Keyed by YYYY-MM-DD
}

export interface WeeklyTotalsDay {
  total_hours: number
  billable_hours?: number
  billable_amount?: string | null
}

export interface WeeklyTotals {
  by_day: Record<string, WeeklyTotalsDay>
  grand_total_hours: number
  grand_total_billable_hours?: number
  grand_total_billable_amount?: string | null
}

export interface WeeklyReportData {
  date_from: string
  date_to: string
  days: string[] // List of YYYY-MM-DD strings
  rows: WeeklyUserRow[]
  totals: WeeklyTotals
}

export interface WeeklyReportResponse {
  data: WeeklyReportData
}

export interface SavedReportView {
  id: string
  workspace_id: string
  user_id: string
  name: string
  report_type: 'summary' | 'detailed' | 'weekly'
  filters: Record<string, any>
  created_at: string
  updated_at: string
}

export interface SavedReportViewCreate {
  name: string
  report_type: 'summary' | 'detailed' | 'weekly'
  filters: Record<string, any>
}

// API definition
export const reportsApi = {
  getSummary: (params: SummaryReportParams) =>
    apiClient.get<SummaryReportResponse>('/reports/summary', { params }),
    
  getDetailed: (params: DetailedReportParams) => 
    apiClient.get<DetailedReportResponse>('/reports/detailed', { params }),
    
  getWeekly: (params: WeeklyReportParams) =>
    apiClient.get<WeeklyReportResponse>('/reports/weekly', { params }),
    
  listSavedViews: (workspaceId: string) =>
    apiClient.get<SavedReportView[]>('/reports/saved-views', { params: { workspace_id: workspaceId } }),
    
  createSavedView: (workspaceId: string, data: SavedReportViewCreate) =>
    apiClient.post<SavedReportView>('/reports/saved-views', data, { params: { workspace_id: workspaceId } }),
    
  deleteSavedView: (workspaceId: string, viewId: string) =>
    apiClient.delete(`/reports/saved-views/${viewId}`, { params: { workspace_id: workspaceId } }),
}
