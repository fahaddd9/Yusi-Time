"use client"

import { useForm, Controller } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useCreateProject, useUpdateProject, useClients } from "@/features/projects/hooks"
import { ColorPicker } from "@/components/ui/color-picker"
import { toast } from "sonner"
import { useEffect } from "react"

const schema = z.object({
  name: z.string().min(1, "Project name is required"),
  client_id: z.string().optional().nullable(),
  visibility: z.enum(["public", "private"]).default("public"),
  color: z.string().optional().nullable(),
  budget_hours: z.string().optional().nullable(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: any
}

export function CreateProjectDialog({ open, onOpenChange, initialData }: Props) {
  const { data: clientsRes } = useClients()
  const clients = clientsRes?.data || []
  const createProject = useCreateProject()
  const updateProject = useUpdateProject()
  const isEditing = !!initialData

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      client_id: null,
      visibility: "public",
      color: null,
      budget_hours: null,
    }
  })

  useEffect(() => {
    if (open) {
      if (initialData) {
        reset({
          name: initialData.name || "",
          client_id: initialData.client_id || null,
          visibility: initialData.visibility || "public",
          color: initialData.color || null,
          budget_hours: initialData.budget_hours ? String(initialData.budget_hours) : null,
        })
      } else {
        reset({
          name: "",
          client_id: null,
          visibility: "public",
          color: null,
          budget_hours: null,
        })
      }
    }
  }, [open, initialData, reset])

  const onSubmit = (data: FormValues) => {
    const payload = {
      ...data,
      client_id: data.client_id === "none" ? null : data.client_id,
      budget_hours: data.budget_hours ? parseFloat(data.budget_hours) : null,
    }

    if (isEditing) {
      updateProject.mutate({ id: initialData.id, data: payload }, {
        onSuccess: () => {
          toast.success("Project updated")
          onOpenChange(false)
        },
        onError: (err: any) => {
          toast.error(err.response?.data?.detail || "Failed to update project")
        }
      })
    } else {
      createProject.mutate(payload, {
        onSuccess: () => {
          toast.success("Project created")
          reset()
          onOpenChange(false)
        },
        onError: (err: any) => {
          toast.error(err.response?.data?.detail || "Failed to create project")
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
          <DialogTitle>{isEditing ? "Edit Project" : "Create Project"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Project Name <span className="text-red-500">*</span></Label>
            <Input id="name" {...register("name")} placeholder="e.g. Website Redesign" />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>Client</Label>
            <Controller
              name="client_id"
              control={control}
              render={({ field }) => (
                <Select value={field.value || "none"} onValueChange={(val) => field.onChange(val)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a client">
                      {field.value && field.value !== "none"
                        ? clients.find(c => c.id === field.value)?.name || "Select a client"
                        : "No Client"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Client</SelectItem>
                    {clients.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Visibility</Label>
              <Controller
                name="visibility"
                control={control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">Public to Workspace</SelectItem>
                      <SelectItem value="private">Private (Invite only)</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Theme Color</Label>
              <Controller
                name="color"
                control={control}
                render={({ field }) => (
                  <ColorPicker color={field.value} onChange={field.onChange} />
                )}
              />
            </div>

            <div className="space-y-2 col-span-2">
              <Label htmlFor="budget_hours">Budget (Hours)</Label>
              <Input id="budget_hours" type="number" step="0.5" min="0" {...register("budget_hours")} placeholder="e.g. 50" />
            </div>
          </div>

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createProject.isPending || updateProject.isPending} className="bg-brand-orange hover:bg-brand-orange-hover text-white">
              {isEditing ? (updateProject.isPending ? "Saving..." : "Save Changes") : (createProject.isPending ? "Creating..." : "Create Project")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
