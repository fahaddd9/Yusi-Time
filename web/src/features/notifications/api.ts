import { apiClient } from '@/lib/api-client'

export interface Notification {
  id: string
  user_id: string
  title: string
  message: string
  event_type: string
  is_read: boolean
  read_at: string | null
  metadata: Record<string, any>
  created_at: string
}

export interface NotificationsResponse {
  data: Notification[]
  total: number
  unread_count: number
  page: number
  per_page: number
}

export interface ListNotificationsParams {
  workspace_id: string
  unread_only?: boolean
  page?: number
  per_page?: number
}

export const notificationsApi = {
  listNotifications: (params: ListNotificationsParams) =>
    apiClient.get<NotificationsResponse>('/notifications', { params }),

  markRead: (ids: string[]) =>
    apiClient.post<{ message: string }>('/notifications/read', { ids }),

  markAllRead: (workspaceId: string) =>
    apiClient.post<{ message: string }>('/notifications/read-all', null, {
      params: { workspace_id: workspaceId },
    }),
}
