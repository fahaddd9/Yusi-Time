import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  reportsApi,
  SummaryReportParams,
  DetailedReportParams,
  WeeklyReportParams,
  SavedReportViewCreate
} from '../api'
import { toast } from 'sonner'

export const reportKeys = {
  all: ['reports'] as const,
  summary: (params: SummaryReportParams) => [...reportKeys.all, 'summary', params] as const,
  detailed: (params: DetailedReportParams) => [...reportKeys.all, 'detailed', params] as const,
  weekly: (params: WeeklyReportParams) => [...reportKeys.all, 'weekly', params] as const,
  savedViews: (workspaceId: string) => [...reportKeys.all, 'savedViews', workspaceId] as const,
}

export function useSummaryReport(params: SummaryReportParams) {
  return useQuery({
    queryKey: reportKeys.summary(params),
    queryFn: async () => {
      const response = await reportsApi.getSummary(params)
      return response.data
    },
    enabled: !!params.workspace_id && !!params.date_from && !!params.date_to,
  })
}

export function useDetailedReport(params: DetailedReportParams) {
  return useQuery({
    queryKey: reportKeys.detailed(params),
    queryFn: async () => {
      const response = await reportsApi.getDetailed(params)
      return response.data
    },
    enabled: !!params.workspace_id && !!params.date_from && !!params.date_to,
  })
}

export function useWeeklyReport(params: WeeklyReportParams) {
  return useQuery({
    queryKey: reportKeys.weekly(params),
    queryFn: async () => {
      const response = await reportsApi.getWeekly(params)
      return response.data.data
    },
    enabled: !!params.workspace_id && !!params.date_from && !!params.date_to,
  })
}

export function useSavedViews(workspaceId: string) {
  return useQuery({
    queryKey: reportKeys.savedViews(workspaceId),
    queryFn: async () => {
      const response = await reportsApi.listSavedViews(workspaceId)
      return response.data
    },
    enabled: !!workspaceId,
  })
}

export function useCreateSavedView() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ workspaceId, data }: { workspaceId: string; data: SavedReportViewCreate }) =>
      reportsApi.createSavedView(workspaceId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: reportKeys.savedViews(variables.workspaceId) })
      toast.success('View saved successfully')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to save view')
    }
  })
}

export function useDeleteSavedView() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ workspaceId, viewId }: { workspaceId: string; viewId: string }) =>
      reportsApi.deleteSavedView(workspaceId, viewId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: reportKeys.savedViews(variables.workspaceId) })
      toast.success('Saved view deleted')
    },
    onError: (error: any) => {
      toast.error('Failed to delete saved view')
    }
  })
}
