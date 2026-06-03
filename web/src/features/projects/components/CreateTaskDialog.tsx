import { useForm } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateTask, useUpdateTask } from "@/features/projects/hooks"
import { toast } from "sonner"
import { useEffect } from "react"

const schema = z.object({
  name: z.string().min(1, "Task name is required"),
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

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      hourly_rate_cents: null,
    }
  })

  useEffect(() => {
    if (open) {
      if (initialData) {
        reset({
          name: initialData.name || "",
          hourly_rate_cents: initialData.hourly_rate_cents || null,
        })
      } else {
        reset({
          name: "",
          hourly_rate_cents: null,
        })
      }
    }
  }, [open, initialData, reset])

  const onSubmit = (data: FormValues) => {
    const payload = {
      name: data.name,
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
