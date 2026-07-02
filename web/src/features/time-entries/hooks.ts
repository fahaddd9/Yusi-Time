/**
 * Time Entry React Query hooks — Implementation Plan §4.12.
 *
 * Key rules:
 * - useCurrentTimer: staleTime=0, refetchInterval=5000 (polls every 5s)
 * - useStopTimer:    onSuccess → showRoundingToast() MANDATORY
 * - useCreateEntry:  onSuccess → showRoundingToast() MANDATORY
 * - useUpdateEntry:  onSuccess → showRoundingToast() MANDATORY
 * - All mutations invalidate entryKeys and currentTimer key on settle
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { timeEntriesApi, ListEntriesParams, StartTimerPayload, StopTimerPayload, CreateManualEntryPayload, UpdateEntryPayload } from './api'
import { showRoundingToast } from '@/lib/rounding-toast'

// ─── Query key factory — Implementation Plan §4.12 ────────────────────────────

export const entryKeys = {
  all: (wsId: string) => ['time-entries', wsId] as const,
  current: (wsId: string) => ['timer', 'current', wsId] as const,
  list: (wsId: string, params?: object) => ['time-entries', wsId, 'list', params] as const,
  detail: (wsId: string, entryId: string) => ['time-entries', wsId, entryId] as const,
}

// ─── Queries ──────────────────────────────────────────────────────────────────

/**
 * GET /time-entries/current
 * Polls every 5 seconds when window is focused, staleTime=0 ensures
 * we always see the latest elapsed time on re-focus (Blueprint §4.14).
 */
export function useCurrentTimer(workspaceId: string | null) {
  return useQuery({
    queryKey: entryKeys.current(workspaceId ?? ''),
    queryFn: () => timeEntriesApi.getCurrent(workspaceId!).then((r) => r.data.data),
    enabled: !!workspaceId,
    staleTime: 0,
    refetchInterval: 5_000,
    refetchIntervalInBackground: false,
  })
}

/**
 * GET /time-entries — cursor-paginated list.
 */
export function useTimeEntries(params: ListEntriesParams, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: entryKeys.list(params.workspace_id, params),
    queryFn: () => timeEntriesApi.listEntries(params).then((r) => r.data),
    enabled: !!params.workspace_id && (options?.enabled ?? true),
    staleTime: 30_000,
  })
}

/**
 * GET /time-entries/{id}
 */
export function useTimeEntry(workspaceId: string | null, entryId: string | null) {
  return useQuery({
    queryKey: entryKeys.detail(workspaceId ?? '', entryId ?? ''),
    queryFn: () => timeEntriesApi.getEntry(workspaceId!, entryId!).then((r) => r.data.data),
    enabled: !!workspaceId && !!entryId,
    staleTime: 30_000,
  })
}

// ─── Mutations ────────────────────────────────────────────────────────────────

/**
 * POST /time-entries/start
 */
export function useStartTimer(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: StartTimerPayload) =>
      timeEntriesApi.startTimer(workspaceId, payload).then((r) => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: entryKeys.current(workspaceId) })
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
    },
    onError: (err: any) => {
      const code = err?.response?.data?.code
      if (code === 'TIMER_ALREADY_RUNNING') {
        toast.error('A timer is already running')
      } else {
        toast.error(err?.response?.data?.detail ?? 'Failed to start timer')
      }
    },
  })
}

/**
 * POST /time-entries/{id}/stop
 * MANDATORY: showRoundingToast() in onSuccess (Implementation Plan §4.12).
 */
export function useStopTimer(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, payload }: { entryId: string; payload?: StopTimerPayload }) =>
      timeEntriesApi.stopTimer(workspaceId, entryId, payload).then((r) => r.data),
    onSuccess: (data) => {
      // MANDATORY rounding toast
      showRoundingToast(data.rounding)
      qc.invalidateQueries({ queryKey: entryKeys.current(workspaceId) })
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
      qc.invalidateQueries({ queryKey: ['time-entries', workspaceId, 'list'] })
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Failed to stop timer')
    },
  })
}

/**
 * POST /time-entries (manual entry)
 * MANDATORY: showRoundingToast() in onSuccess.
 */
export function useCreateEntry(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateManualEntryPayload) =>
      timeEntriesApi.createEntry(workspaceId, payload).then((r) => r.data),
    onSuccess: (data) => {
      // MANDATORY rounding toast
      showRoundingToast(data.rounding)
      if (data.has_overlap) {
        toast.warning('This entry overlaps with an existing entry', { duration: 4000 })
      }
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
      qc.invalidateQueries({ queryKey: ['time-entries', workspaceId, 'list'] })
    },
    onError: (err: any) => {
      const code = err?.response?.data?.code
      if (code === 'PAST_ENTRY_LIMIT_EXCEEDED') {
        toast.error('Entry exceeds the workspace backdating limit')
      } else {
        toast.error(err?.response?.data?.detail ?? 'Failed to create entry')
      }
    },
  })
}

/**
 * PATCH /time-entries/{id}
 * MANDATORY: showRoundingToast() in onSuccess.
 */
export function useUpdateEntry(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, payload }: { entryId: string; payload: UpdateEntryPayload }) =>
      timeEntriesApi.updateEntry(workspaceId, entryId, payload).then((r) => r.data),
    onSuccess: (data, { entryId }) => {
      // MANDATORY rounding toast
      showRoundingToast(data.rounding)
      qc.invalidateQueries({ queryKey: entryKeys.detail(workspaceId, entryId) })
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
      qc.invalidateQueries({ queryKey: ['time-entries', workspaceId, 'list'] })
    },
    onError: (err: any) => {
      const code = err?.response?.data?.code
      if (code === 'ENTRY_LOCKED') {
        toast.error('This entry is locked and cannot be edited')
      } else {
        const detail = err?.response?.data?.detail
        const msg = Array.isArray(detail) ? detail[0]?.msg : detail
        toast.error(msg ?? 'Failed to update entry')
      }
    },
  })
}

/**
 * DELETE /time-entries/{id}
 */
export function useDeleteEntry(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (entryId: string) =>
      timeEntriesApi.deleteEntry(workspaceId, entryId).then((r) => r.data),
    onSuccess: () => {
      toast.success('Entry deleted')
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
    },
    onError: (err: any) => {
      const code = err?.response?.data?.code
      if (code === 'ENTRY_LOCKED') {
        toast.error('This entry is locked and cannot be deleted')
      } else {
        toast.error(err?.response?.data?.detail ?? 'Failed to delete entry')
      }
    },
  })
}

/**
 * POST /time-entries/submit
 * Bulk-transitions draft entries to pending status (Submit Week).
 */
export function useSubmitEntries(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (entryIds: string[]) =>
      timeEntriesApi.submitEntries(workspaceId, entryIds).then((r) => r.data),
    onSuccess: (data) => {
      toast.success(`Submitted ${data.count} ${data.count === 1 ? 'entry' : 'entries'} for approval`)
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Failed to submit entries')
    },
  })
}

/**
 * POST /time-entries/{id}/continue
 */
export function useContinueEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, workspaceId, force = false }:
      { entryId: string; workspaceId: string; force?: boolean }) =>
      timeEntriesApi.continue(entryId, { workspaceId, force }),
    onSuccess: (_, { workspaceId }) => {
      qc.invalidateQueries({ queryKey: entryKeys.current(workspaceId) })
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
    },
    onError: (err: any) => {
      const code = err?.response?.data?.code
      if (code === 'TIMER_ALREADY_RUNNING') {
        toast.error('A timer is already running')
      } else {
        toast.error(err?.response?.data?.detail ?? 'Failed to continue entry')
      }
    },
  })
}

/**
 * POST /time-entries/{id}/duplicate
 * MANDATORY: showRoundingToast() in onSuccess.
 */
export function useDuplicateEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, workspaceId }:
      { entryId: string; workspaceId: string }) =>
      timeEntriesApi.duplicate(entryId, { workspaceId }),
    onSuccess: (response, { workspaceId }) => {
      // MANDATORY rounding toast
      showRoundingToast(response.data.rounding)
      qc.invalidateQueries({ queryKey: entryKeys.all(workspaceId) })
      qc.invalidateQueries({ queryKey: ['time-entries', workspaceId, 'list'] })
      // DR-30: also invalidate reports so the new entry appears immediately in the Detailed Report
      qc.invalidateQueries({ queryKey: ['reports'] })
      toast.success('Entry duplicated')
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Failed to duplicate entry')
    },
  })
}
