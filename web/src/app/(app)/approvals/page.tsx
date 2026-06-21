'use client'

import { useWorkspaceStore } from '@/stores/workspace-store'
import { useWorkspace } from '@/features/settings/hooks'
import { ApprovalList } from '@/features/approvals/components/ApprovalList'

export default function ApprovalsPage() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspace } = useWorkspace(activeWorkspaceId)

  // Wait for workspace to load to ensure we only show for workflow_enabled workspaces
  if (!workspace) return null

  if (!workspace.approval_workflow_enabled) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8">
        <h2 className="text-xl font-semibold text-foreground mb-2">Approvals Disabled</h2>
        <p>The approval workflow is not enabled for this workspace.</p>
        <p className="mt-1 text-sm">An admin can enable it in Workspace Settings.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Timesheet Approvals</h1>
        <p className="text-muted-foreground mt-1">
          Review and approve pending timesheets submitted by your team.
        </p>
      </div>

      <ApprovalList workspaceId={activeWorkspaceId ?? ''} />
    </div>
  )
}
