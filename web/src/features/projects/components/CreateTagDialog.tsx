"use client"

import { useForm, Controller } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateTag, useUpdateTag } from "@/features/projects/hooks"
import { ColorPicker } from "@/components/ui/color-picker"
import { toast } from "sonner"
import { useEffect } from "react"

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  color: z.string().optional().nullable(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: any
}

export function CreateTagDialog({ open, onOpenChange, initialData }: Props) {
  const createTag = useCreateTag()
  const updateTag = useUpdateTag()

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      color: null,
    }
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        color: initialData.color || null,
      })
    } else {
      reset({
        name: "",
        color: null,
      })
    }
  }, [initialData, reset])

  const isEdit = !!initialData

  const onSubmit = (data: FormValues) => {
    if (isEdit) {
      updateTag.mutate({ id: initialData.id, data }, {
        onSuccess: () => {
          toast.success("Tag updated")
          onOpenChange(false)
        },
        onError: (err: any) => {
          const detail = err.response?.data?.detail;
          const msg = typeof detail === 'string' ? detail : detail?.detail || "Failed to update tag";
          toast.error(msg)
        }
      })
    } else {
      createTag.mutate(data, {
        onSuccess: () => {
          toast.success("Tag created")
          onOpenChange(false)
        },
        onError: (err: any) => {
          const detail = err.response?.data?.detail;
          const msg = typeof detail === 'string' ? detail : detail?.detail || "Failed to create tag";
          toast.error(msg)
        }
      })
    }
  }

  const isPending = createTag.isPending || updateTag.isPending

  return (
    <Dialog open={open} onOpenChange={(val) => {
      onOpenChange(val)
      if (!val) reset()
    }}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Tag" : "Add Tag"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name <span className="text-red-500">*</span></Label>
            <Input id="name" {...register("name")} placeholder="Tag name" />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
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

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending} className="bg-brand-orange hover:bg-brand-orange-hover text-white">
              {isPending ? "Saving..." : isEdit ? "Save Changes" : "Add Tag"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
