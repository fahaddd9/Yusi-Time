import { useState } from "react"
import { useTasks, useDeleteTask } from "@/features/projects/hooks"
import { Button } from "@/components/ui/button"
import { Plus, Trash2, Edit2 } from "lucide-react"
import { CreateTaskDialog } from "./CreateTaskDialog"

export function TaskTable({ projectId }: { projectId: string }) {
  const { data: tasksRes, isLoading } = useTasks(projectId)
  const deleteTask = useDeleteTask()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<any>(null)

  const tasks = tasksRes?.data || []

  if (isLoading) {
    return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-orange mx-auto my-8"></div>
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Tasks</h3>
        <Button onClick={() => setIsCreateOpen(true)} size="sm" className="bg-brand-orange hover:bg-brand-orange-hover text-white">
          <Plus className="w-4 h-4 mr-2" />
          Add Task
        </Button>
      </div>

      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {tasks.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No tasks found for this project.
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-6 py-4 font-medium">Task Name</th>
                <th className="px-6 py-4 font-medium">Assignee</th>
                <th className="px-6 py-4 font-medium text-right">Hourly Rate</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {tasks.map((task) => (
                <tr key={task.id} className="hover:bg-muted/30 transition-colors group">
                  <td className="px-6 py-4 font-medium">{task.name}</td>
                  <td className="px-6 py-4 text-muted-foreground">
                    {task.assignee_user_id ? 'Assigned' : 'Unassigned'}
                  </td>
                  <td className="px-6 py-4 text-right text-muted-foreground">
                    {task.hourly_rate_cents ? `$${(task.hourly_rate_cents / 100).toFixed(2)}/h` : 'Project Default'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
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
                    </div>
                  </td>
                </tr>
              ))}
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
