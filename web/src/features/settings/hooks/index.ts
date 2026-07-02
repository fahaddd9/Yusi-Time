/**
 * Settings hooks — React Query wrappers for workspace, member, and invite operations.
 *
 * All mutations invalidate relevant query keys on success.
 * Workspace queries use short staleTime (30s) so settings/role changes propagate instantly.
 */
'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  settingsApi,
  type InviteCreateRequest,
  type UserUpdate,
  type WorkspaceUpdate,
} from '../api'

// ── Query keys ─────────────────────────────────────────────────────────────────

export const workspaceKeys = {
  all: ['workspaces'] as const,
  list: () => [...workspaceKeys.all, 'list'] as const,
  detail: (id: string) => [...workspaceKeys.all, 'detail', id] as const,
  members: (id: string) => [...workspaceKeys.all, 'members', id] as const,
  invites: (id: string) => [...workspaceKeys.all, 'invites', id] as const,
}

export const userKeys = {
  me: ['user', 'me'] as const,
}

// ── Workspace hooks ────────────────────────────────────────────────────────────

export function useWorkspaces() {
  return useQuery({
    queryKey: workspaceKeys.list(),
    queryFn: () => settingsApi.listWorkspaces().then((r) => r.data),
    staleTime: 30 * 1000,
  })
}

export function useWorkspace(workspaceId: string | null) {
  return useQuery({
    queryKey: workspaceKeys.detail(workspaceId ?? ''),
    queryFn: () => settingsApi.getWorkspace(workspaceId!).then((r) => r.data),
    staleTime: 30 * 1000,
    enabled: !!workspaceId,
  })
}

export function useUpdateWorkspace(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: WorkspaceUpdate) => settingsApi.updateWorkspace(workspaceId, data),
    onSuccess: (response) => {
      queryClient.setQueryData(workspaceKeys.detail(workspaceId), response.data)
      queryClient.invalidateQueries({ queryKey: workspaceKeys.list() })
      // Invalidate downstream consumers that depend on workspace settings
      // (is_billable, currency, rounding_mode, attendance_enabled, etc.)
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['time-entries'] })
      queryClient.invalidateQueries({ queryKey: ['attendance'] })
      toast.success('Workspace updated')
    },
    onError: () => {
      toast.error('Failed to update workspace')
    },
  })
}

export function useDeleteWorkspace(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => settingsApi.deleteWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.list() })
      toast.success('Workspace deleted')
    },
    onError: () => {
      toast.error('Failed to delete workspace')
    },
  })
}

// ── Members hooks ──────────────────────────────────────────────────────────────

export function useWorkspaceMembers(workspaceId: string, page = 1, perPage = 25) {
  return useQuery({
    queryKey: [...workspaceKeys.members(workspaceId), page, perPage],
    queryFn: () => settingsApi.listMembers(workspaceId, page, perPage).then((r) => r.data),
    staleTime: 30 * 1000,
    enabled: !!workspaceId,
  })
}

export function useChangeRole(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, newRole }: { userId: string; newRole: string }) =>
      settingsApi.changeRole(workspaceId, userId, newRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(workspaceId) })
      // Workspace list includes role for the current user — must refresh
      queryClient.invalidateQueries({ queryKey: workspaceKeys.list() })
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['time-entries'] })
      toast.success('Role updated')
    },
    onError: (error: any) => {
      const code = error?.response?.data?.code
      if (code === 'SOLE_ADMIN') {
        toast.error('Cannot demote the sole Admin')
      } else if (code === 'BAD_REQUEST') {
        toast.error('Cannot promote to admin role')
      } else {
        toast.error('Failed to update role')
      }
    },
  })
}

export function useRemoveMember(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => settingsApi.removeMember(workspaceId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(workspaceId) })
      toast.success('Member removed')
    },
    onError: (error: any) => {
      const code = error?.response?.data?.code
      if (code === 'SOLE_ADMIN') {
        toast.error('Cannot remove the sole Admin')
      } else {
        toast.error('Failed to remove member')
      }
    },
  })
}

// ── Invite hooks ───────────────────────────────────────────────────────────────

export function useInvites(workspaceId: string) {
  return useQuery({
    queryKey: workspaceKeys.invites(workspaceId),
    queryFn: () => settingsApi.listInvites(workspaceId).then((r) => r.data),
    staleTime: 60 * 1000,
    enabled: !!workspaceId,
  })
}

export function useCreateInvite(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: InviteCreateRequest) => settingsApi.createInvite(workspaceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.invites(workspaceId) })
    },
    onError: () => {
      toast.error('Failed to create invite')
    },
  })
}

export function useRevokeInvite(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (token: string) => settingsApi.revokeInvite(workspaceId, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.invites(workspaceId) })
      toast.success('Invite revoked')
    },
    onError: () => {
      toast.error('Failed to revoke invite')
    },
  })
}

export function useGetInvitePublic(token: string | null) {
  return useQuery({
    queryKey: ['invite', 'public', token],
    queryFn: () => settingsApi.getInvitePublic(token!).then((r) => r.data),
    enabled: !!token,
    retry: false,
  })
}

export function useAcceptInvite() {
  return useMutation({
    mutationFn: (token: string) => settingsApi.acceptInvite(token),
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || 'Failed to accept invite'
      toast.error(msg)
    },
  })
}

// ── User hooks ─────────────────────────────────────────────────────────────────

export function useMe() {
  return useQuery({
    queryKey: userKeys.me,
    queryFn: () => settingsApi.getMe().then((r) => r.data),
    staleTime: 60 * 1000,
  })
}

export function useUpdateMe() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UserUpdate) => settingsApi.updateMe(data),
    onSuccess: (response) => {
      queryClient.setQueryData(userKeys.me, response.data)
      toast.success('Profile updated')
    },
    onError: () => {
      toast.error('Failed to update profile')
    },
  })
}
