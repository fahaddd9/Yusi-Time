/**
 * Workspace store — tracks which workspace is currently active.
 *
 * Clears the React Query cache on workspace switch so stale data
 * from the previous workspace never bleeds through.
 *
 * Blueprint v2.0 G2 · IMPLEMENTATION_PLAN Phase 2 Step 2.8.
 */
import { create } from 'zustand'
import { getQueryClient } from '@/lib/query-client'

interface WorkspaceStore {
  activeWorkspaceId: string | null
  setWorkspaceId: (id: string) => void
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  activeWorkspaceId: null,
  setWorkspaceId: (id) => {
    set({ activeWorkspaceId: id })
    // Invalidate ALL cached queries when switching workspaces.
    // Every piece of data (members, projects, timesheets) is workspace-scoped.
    getQueryClient().clear()
  },
}))
