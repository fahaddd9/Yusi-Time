import { useState } from "react"
import { useProjectMembers, useAddProjectMember, useRemoveProjectMember } from "@/features/projects/hooks"
import { useWorkspaceMembers } from "@/features/settings/hooks"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { Button } from "@/components/ui/button"
import { Trash2, UserPlus, Users } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"

export function ProjectMembers({ projectId, isManagerOrAdmin }: { projectId: string, isManagerOrAdmin?: boolean }) {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: membersRes, isLoading: membersLoading } = useProjectMembers(projectId)
  const { data: wsMembersRes, isLoading: wsMembersLoading } = useWorkspaceMembers(activeWorkspaceId ?? '')
  
  const addMember = useAddProjectMember()
  const removeMember = useRemoveProjectMember()

  const [selectedUser, setSelectedUser] = useState<string>("")

  const projectMembers = membersRes || []
  const wsMembers = wsMembersRes?.items || []

  const unassignedMembers = wsMembers.filter(wm => 
    wm.role === 'member' && !projectMembers.some(pm => pm.user_id === wm.user_id)
  )

  const handleAdd = () => {
    if (!selectedUser) return
    addMember.mutate({ projectId, userId: selectedUser }, {
      onSuccess: () => {
        toast.success("Member added to project")
        setSelectedUser("")
      },
      onError: (err: any) => {
        toast.error(err.response?.data?.detail || "Failed to add member")
      }
    })
  }

  const handleRemove = (userId: string) => {
    if (confirm("Remove this member from the project?")) {
      removeMember.mutate({ projectId, userId }, {
        onSuccess: () => {
          toast.success("Member removed")
        },
        onError: (err: any) => {
          toast.error(err.response?.data?.detail || "Failed to remove member")
        }
      })
    }
  }

  if (membersLoading || wsMembersLoading) {
    return <Skeleton className="h-40 w-full" />
  }

  return (
    <div className="space-y-6">
      {isManagerOrAdmin && unassignedMembers.length > 0 && (
        <div className="bg-card border border-border p-6 rounded-xl shadow-sm flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1 w-full space-y-1.5">
            <label className="text-sm font-medium">Add Workspace Member</label>
            <Select value={selectedUser} onValueChange={(val) => setSelectedUser(val || "")}>
              <SelectTrigger>
                <SelectValue placeholder="Select a member...">
                  {selectedUser ? unassignedMembers.find(m => m.user_id === selectedUser)?.full_name : "Select a member..."}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {unassignedMembers.map(m => (
                  <SelectItem key={m.user_id} value={m.user_id}>
                    {m.full_name} ({m.email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleAdd} disabled={!selectedUser || addMember.isPending} className="bg-brand-orange hover:bg-brand-orange-hover text-white w-full sm:w-auto">
            <UserPlus className="w-4 h-4 mr-2" />
            Add to Project
          </Button>
        </div>
      )}

      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {projectMembers.length === 0 ? (
          <div className="p-12 flex flex-col items-center text-center text-muted-foreground">
            <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center mb-4">
              <Users className="w-6 h-6 text-muted-foreground opacity-50" />
            </div>
            <h4 className="text-base font-semibold text-foreground mb-1">No members assigned</h4>
            <p className="text-sm max-w-sm">This is a private project but no specific members have been invited yet.</p>
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-6 py-4 font-medium">Member</th>
                <th className="px-6 py-4 font-medium">Role in Workspace</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {projectMembers.map((pm) => {
                const wm = wsMembers.find(m => m.user_id === pm.user_id)
                if (!wm) return null
                return (
                  <tr key={pm.user_id} className="hover:bg-muted/30 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="text-xs bg-brand-orange/10 text-brand-orange">
                            {wm.full_name.substring(0, 2).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">{wm.full_name}</span>
                          <span className="text-xs text-muted-foreground">{wm.email}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground capitalize">
                      {wm.role}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                        {isManagerOrAdmin && (
                          <Button 
                            variant="ghost" 
                            size="icon-sm" 
                            className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => handleRemove(pm.user_id)}
                            disabled={removeMember.isPending}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
