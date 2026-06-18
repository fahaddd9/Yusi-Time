import { useForm, Controller } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useCreateTask, useUpdateTask } from "@/features/projects/hooks"
import { useWorkspaceMembers } from "@/features/settings/hooks"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { toast } from "sonner"
import { useEffect } from "react"

const schema = z.object({
  name: z.string().min(1, "Task name is required"),
  assignee_user_id: z.string().optional().nullable(),
  estimated_hours: z.string().optional().nullable(),
  billable_override: z.boolean().optional().nullable(),
  hourly_rate_cents: z.number().nullable().optional(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  projectId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: any
}

export function CreateTaskDialog({ projectId, open, onOpenChange, initialData }: Props) {
  const createTask = useCreateTask()
  const updateTask = useUpdateTask()
  const isEditing = !!initialData
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: membersData } = useWorkspaceMembers(activeWorkspaceId ?? '')
  const members = membersData?.items || []

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      assignee_user_id: null,
      estimated_hours: null,
      billable_override: null,
      hourly_rate_cents: null,
    }
  })

  useEffect(() => {
    if (open) {
      if (initialData) {
        reset({
          name: initialData.name || "",
          assignee_user_id: initialData.assignee_user_id || null,
          estimated_hours: initialData.estimated_hours ? String(initialData.estimated_hours) : null,
          billable_override: initialData.billable_override ?? null,
          hourly_rate_cents: initialData.hourly_rate_cents || null,
        })
      } else {
        reset({
          name: "",
          assignee_user_id: null,
          estimated_hours: null,
          billable_override: null,
          hourly_rate_cents: null,
        })
      }
    }
  }, [open, initialData, reset])

  const onSubmit = (data: FormValues) => {
    const payload = {
      name: data.name,
      assignee_user_id: data.assignee_user_id || null,
      estimated_hours: data.estimated_hours ? parseFloat(data.estimated_hours) : null,
      billable_override: data.billable_override,
      hourly_rate_cents: data.hourly_rate_cents || null,
    }

    if (isEditing) {
      updateTask.mutate({ id: initialData.id, projectId, data: payload }, {
        onSuccess: () => {
          toast.success("Task updated")
          onOpenChange(false)
        },
        onError: (err: any) => {
          toast.error(err.response?.data?.detail || "Failed to update task")
        }
      })
    } else {
      createTask.mutate({ ...payload, project_id: projectId }, {
        onSuccess: () => {
          toast.success("Task created")
          reset()
          onOpenChange(false)
        },
        onError: (err: any) => {
          toast.error(err.response?.data?.detail || "Failed to create task")
        }
      })
    }
  }

  return (
    <Dialog open={open} onOpenChange={(val) => {
      onOpenChange(val)
      if (!val) reset()
    }}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Task" : "Add Task"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Task Name <span className="text-red-500">*</span></Label>
            <Input id="name" {...register("name")} placeholder="e.g. Design Wireframes" />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>Assignee</Label>
            <Controller
              name="assignee_user_id"
              control={control}
              render={({ field }) => (
                <Select value={field.value || "none"} onValueChange={(val) => field.onChange(val === "none" ? null : val)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select member">
                      {field.value && field.value !== "none"
                        ? members.find(m => m.user_id === field.value)?.full_name || "Select member"
                        : "Unassigned"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Unassigned</SelectItem>
                    {members.map(m => (
                      <SelectItem key={m.user_id} value={m.user_id}>{m.full_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="estimated_hours">Estimated Hours</Label>
              <Input id="estimated_hours" type="number" step="0.5" min="0" {...register("estimated_hours")} placeholder="e.g. 10" />
            </div>
            
            <div className="space-y-2">
              <Label>Billable Override</Label>
              <Controller
                name="billable_override"
                control={control}
                render={({ field }) => (
                  <Select value={field.value === true ? "true" : field.value === false ? "false" : "null"} onValueChange={(val) => field.onChange(val === "null" ? null : val === "true")}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="null">Inherit from Project</SelectItem>
                      <SelectItem value="true">Always Billable</SelectItem>
                      <SelectItem value="false">Non-Billable</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="hourly_rate">Custom Hourly Rate ($)</Label>
            <Input 
              id="hourly_rate" 
              type="number" 
              step="0.01" 
              placeholder="Leave empty to use project default"
              {...register("hourly_rate_cents", {
                setValueAs: (v) => v === "" ? null : Math.round(parseFloat(v) * 100)
              })} 
            />
            {errors.hourly_rate_cents && <p className="text-xs text-red-500">{errors.hourly_rate_cents.message}</p>}
          </div>

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createTask.isPending || updateTask.isPending} className="bg-brand-orange hover:bg-brand-orange-hover text-white">
              {isEditing ? (updateTask.isPending ? "Saving..." : "Save Changes") : (createTask.isPending ? "Creating..." : "Add Task")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
