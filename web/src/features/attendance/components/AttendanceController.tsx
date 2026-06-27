'use client'
/**
 * AttendanceController — Phase 6.5, Addendum §6.1.
 *
 * A thin layout-level component that:
 *   1. Reads the active workspace's attendance settings from useWorkspace()
 *   2. Calls useWorkStartTrigger() to poll for F1 notifications (Member only)
 *   3. Renders WorkStartModal (always mounted, visibility driven by attendance store)
 *
 * Mounted once in (app)/layout.tsx alongside IdleModal. Keeps the layout file
 * clean by encapsulating all attendance-related concerns here.
 *
 * PRD-ADD-03: Admin/Manager roles never see the modal — the trigger hook
 * suppresses itself when role !== 'member'.
 */

import { WorkStartModal } from './WorkStartModal'
import { LogoutGuardDialog } from './LogoutGuardDialog'
import { useWorkStartTrigger } from '../hooks/useWorkStartTrigger'
import { useWorkspace, useWorkspaces } from '@/features/settings/hooks'
import { useWorkspaceStore } from '@/stores/workspace-store'

export function AttendanceController() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()
  const { data: workspace } = useWorkspace(activeWorkspaceId)

  const role = workspaces?.find((w: any) => w.id === activeWorkspaceId)?.role
  
  const isLoaded = workspace !== undefined && role !== undefined
  const attendanceEnabled = workspace?.attendance_enabled ?? false
  const attendanceMode = workspace?.attendance_mode ?? 'fixed_schedule'

  // Activate the F1 trigger polling (Member only, suppressed for Admin/Manager)
  // Only enable when we are sure data has loaded to prevent race conditions
  useWorkStartTrigger({
    workspaceId: activeWorkspaceId ?? '',
    role: role ?? 'viewer',
    attendanceMode,
    attendanceEnabled: isLoaded ? attendanceEnabled : false,
    workStartTime: workspace?.work_start_time,
  })

  // Always render modals — visibility is driven by attendance-store state
  return (
    <>
      <WorkStartModal />
      <LogoutGuardDialog />
    </>
  )
}
