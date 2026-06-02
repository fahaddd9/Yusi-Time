/**
 * Settings API — typed functions for workspace, member, and invite operations.
 *
 * All calls go through the shared apiClient which handles:
 *  - Auth token attachment (Authorization: Bearer <token>)
 *  - Silent refresh on 401 with HttpOnly cookie
 *  - Redirect to /login on complete auth failure
 *
 * API Spec v1.1 §4–7 · Phase 2.
 */
import { apiClient } from '@/lib/api-client'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface WorkspaceListItem {
  id: string
  name: string
  logo_url: string | null
  role: string
  member_count: number
  created_at: string
}

export interface WorkspaceDetail {
  id: string
  name: string
  logo_url: string | null
  default_timezone: string
  date_format: string
  currency: string
  default_hourly_rate_cents: number | null
  rounding_mode: string
  rounding_interval_minutes: number | null
  mandatory_description: boolean
  max_timer_duration_seconds: number
  past_entry_limit_days: number
  lock_period_days: number
  approval_workflow_enabled: boolean
  idle_detection_enabled: boolean
  idle_timeout_minutes: number | null
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface WorkspaceUpdate {
  name?: string
  logo_url?: string
  default_timezone?: string
  date_format?: string
  currency?: string
  default_hourly_rate_cents?: number
  rounding_mode?: string
  rounding_interval_minutes?: number
  mandatory_description?: boolean
  approval_workflow_enabled?: boolean
  idle_detection_enabled?: boolean
  idle_timeout_minutes?: number
  max_timer_duration_seconds?: number
  past_entry_limit_days?: number
  lock_period_days?: number
}

export interface MemberResponse {
  user_id: string
  email: string
  full_name: string
  avatar_url: string | null
  role: string
  joined_at: string
}

export interface PaginatedMemberResponse {
  items: MemberResponse[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface InviteCreateRequest {
  email: string
  role: 'manager' | 'member' | 'viewer'
}

export interface InviteResponse {
  id: string
  email: string
  role: string
  token: string
  expires_at: string
  used: boolean
  revoked: boolean
  created_at: string
}

export interface InvitePublicResponse {
  workspace_id: string
  workspace_name: string
  workspace_logo_url: string | null
  role: string
  email: string
  expires_at: string
}

export interface PaginatedInviteResponse {
  items: InviteResponse[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface UserPublic {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  timezone: string | null
  weekly_hours_goal: number | null
  is_active: boolean
  is_superadmin: boolean
  created_at: string
  updated_at: string
}

export interface UserUpdate {
  full_name?: string
  avatar_url?: string
  timezone?: string
  weekly_hours_goal?: number
}

// ── Workspace API ──────────────────────────────────────────────────────────────

export const settingsApi = {
  // Workspaces
  listWorkspaces: () =>
    apiClient.get<WorkspaceListItem[]>('/workspaces'),

  getWorkspace: (id: string) =>
    apiClient.get<WorkspaceDetail>(`/workspaces/${id}`),

  updateWorkspace: (id: string, data: WorkspaceUpdate) =>
    apiClient.patch<WorkspaceDetail>(`/workspaces/${id}`, data),

  deleteWorkspace: (id: string) =>
    apiClient.delete(`/workspaces/${id}`),

  // Members
  listMembers: (workspaceId: string, page = 1, perPage = 25) =>
    apiClient.get<PaginatedMemberResponse>(
      `/workspaces/${workspaceId}/members?page=${page}&per_page=${perPage}`
    ),

  changeRole: (workspaceId: string, userId: string, newRole: string) =>
    apiClient.patch<MemberResponse>(
      `/workspaces/${workspaceId}/members/${userId}`,
      { new_role: newRole }
    ),

  removeMember: (workspaceId: string, userId: string) =>
    apiClient.delete(`/workspaces/${workspaceId}/members/${userId}`),

  // Invites
  createInvite: (workspaceId: string, data: InviteCreateRequest) =>
    apiClient.post<InviteResponse>(`/workspaces/${workspaceId}/invites`, data),

  listInvites: (workspaceId: string, page = 1, perPage = 25) =>
    apiClient.get<PaginatedInviteResponse>(
      `/workspaces/${workspaceId}/invites?page=${page}&per_page=${perPage}`
    ),

  revokeInvite: (workspaceId: string, token: string) =>
    apiClient.delete(`/workspaces/${workspaceId}/invites/${token}`),

  getInvitePublic: (token: string) =>
    apiClient.get<InvitePublicResponse>(`/invites/${token}`),

  acceptInvite: (token: string) =>
    apiClient.post(`/invites/${token}/accept`),

  // Users
  getMe: () =>
    apiClient.get<UserPublic>('/users/me'),

  updateMe: (data: UserUpdate) =>
    apiClient.patch<UserPublic>('/users/me', data),

  deleteMe: () =>
    apiClient.delete('/users/me'),
}
