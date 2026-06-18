import { useState, useMemo } from "react"
import { useTasks, useDeleteTask } from "@/features/projects/hooks"
import { useWorkspaceMembers } from "@/features/settings/hooks"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useTimeEntries } from "@/features/time-entries/hooks"
import { Button } from "@/components/ui/button"
import { Plus, Trash2, Edit2, ClipboardList } from "lucide-react"
import { CreateTaskDialog } from "./CreateTaskDialog"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

export function TaskTable({ projectId, isManagerOrAdmin }: { projectId: string, isManagerOrAdmin?: boolean }) {
  const { data: tasksRes, isLoading } = useTasks(projectId)
  const deleteTask = useDeleteTask()
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: membersData } = useWorkspaceMembers(activeWorkspaceId ?? '')
  const members = membersData?.items || []
  
  const { data: entriesData } = useTimeEntries({
    workspace_id: activeWorkspaceId ?? '',
    project_id: projectId,
    limit: 1000
  })

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<any>(null)

  const tasks = tasksRes?.data || []

  const loggedHoursByTask = useMemo(() => {
    const map: Record<string, number> = {}
    if (entriesData?.data) {
      entriesData.data.forEach(e => {
        if (e.task_id) {
          map[e.task_id] = (map[e.task_id] || 0) + (e.duration_seconds || 0)
        }
      })
    }
    return map
  }, [entriesData])

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-[200px]" />
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Tasks</h3>
        {isManagerOrAdmin && (
          <Button onClick={() => setIsCreateOpen(true)} size="sm" className="bg-brand-orange hover:bg-brand-orange-hover text-white">
            <Plus className="w-4 h-4 mr-2" />
            Add Task
          </Button>
        )}
      </div>

      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {tasks.length === 0 ? (
          <div className="p-12 flex flex-col items-center text-center text-muted-foreground">
            <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center mb-4">
              <ClipboardList className="w-6 h-6 text-muted-foreground opacity-50" />
            </div>
            <h4 className="text-base font-semibold text-foreground mb-1">No tasks yet</h4>
            <p className="text-sm mb-4 max-w-sm">There are no tasks associated with this project. Add a task to start tracking time against it.</p>
            {isManagerOrAdmin && (
              <Button onClick={() => setIsCreateOpen(true)} variant="outline">
                Add Task
              </Button>
            )}
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-6 py-4 font-medium">Task Name</th>
                <th className="px-6 py-4 font-medium">Assignee</th>
                <th className="px-6 py-4 font-medium text-right">Estimated</th>
                <th className="px-6 py-4 font-medium text-right">Logged</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {tasks.map((task) => {
                const assignee = members.find(m => m.user_id === task.assignee_user_id)
                const logged = (loggedHoursByTask[task.id] || 0) / 3600
                return (
                  <tr key={task.id} className="hover:bg-muted/30 transition-colors group">
                    <td className="px-6 py-4 font-medium">{task.name}</td>
                    <td className="px-6 py-4 text-muted-foreground">
                      {assignee ? (
                        <div className="flex items-center gap-2">
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="text-[10px] bg-brand-orange/10 text-brand-orange">
                              {assignee.full_name.substring(0, 2).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <span>{assignee.full_name}</span>
                        </div>
                      ) : (
                        <span className="text-xs px-2 py-1 bg-muted rounded">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-muted-foreground">
                      {task.estimated_hours ? `${task.estimated_hours}h` : '-'}
                    </td>
                    <td className="px-6 py-4 text-right text-muted-foreground font-mono">
                      {logged > 0 ? `${logged.toFixed(2)}h` : '-'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        {isManagerOrAdmin && (
                          <>
                            <Button variant="ghost" size="icon-sm" className="h-8 w-8" onClick={() => setEditingTask(task)}>
                              <Edit2 className="w-4 h-4 text-muted-foreground" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon-sm" 
                              className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
                              onClick={() => {
                                if (confirm("Delete this task?")) {
                                  deleteTask.mutate({ id: task.id, projectId })
                                }
                              }}
                              disabled={deleteTask.isPending}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </>
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

      <CreateTaskDialog 
        projectId={projectId} 
        open={isCreateOpen || !!editingTask} 
        onOpenChange={(val) => {
          setIsCreateOpen(val)
          if (!val) setEditingTask(null)
        }} 
        initialData={editingTask}
      />
    </div>
  )
}
