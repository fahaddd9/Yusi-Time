import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi, ListNotificationsParams } from '../api'

export const notificationKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationKeys.all, 'list'] as const,
  list: (params: ListNotificationsParams) => [...notificationKeys.lists(), params] as const,
}

export function useNotifications(params: ListNotificationsParams) {
  return useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: async () => {
      const response = await notificationsApi.listNotifications(params)
      return response.data
    },
    enabled: !!params.workspace_id,
    staleTime: 3000,
    refetchInterval: 3000,
  })
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (ids: string[]) => notificationsApi.markRead(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all })
    },
  })
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (workspaceId: string) => notificationsApi.markAllRead(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all })
    },
  })
}
