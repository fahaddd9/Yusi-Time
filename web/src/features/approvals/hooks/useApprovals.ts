import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { approvalsApi, ListPendingParams } from '../api'

export const approvalKeys = {
  all: ['approvals'] as const,
  pendingList: (params: ListPendingParams) => [...approvalKeys.all, 'pending', params] as const,
}

export function usePendingApprovals(params: ListPendingParams) {
  return useQuery({
    queryKey: approvalKeys.pendingList(params),
    queryFn: async () => {
      const response = await approvalsApi.listPending(params)
      return response.data
    },
    enabled: !!params.workspace_id,
  })
}

export function useSubmitWeek() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ workspaceId, weekStart }: { workspaceId: string; weekStart: string }) =>
      approvalsApi.submitWeek(workspaceId, weekStart),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.all })
      queryClient.invalidateQueries({ queryKey: ['time-entries'] })
    },
  })
}

export function useApproveWeek() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ workspaceId, submissionId }: { workspaceId: string; submissionId: string }) =>
      approvalsApi.approveWeek(workspaceId, submissionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.all })
      queryClient.invalidateQueries({ queryKey: ['time-entries'] })
    },
  })
}

export function useRejectWeek() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ workspaceId, submissionId, note }: { workspaceId: string; submissionId: string; note: string }) =>
      approvalsApi.rejectWeek(workspaceId, submissionId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.all })
      queryClient.invalidateQueries({ queryKey: ['time-entries'] })
    },
  })
}
