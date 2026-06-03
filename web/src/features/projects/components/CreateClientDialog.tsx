"use client"

import { useForm } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateClient, useUpdateClient } from "@/features/projects/hooks"
import { toast } from "sonner"
import { useEffect } from "react"

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email").or(z.literal("")).nullable().optional(),
  phone: z.string().nullable().optional(),
  address: z.string().nullable().optional(),
  hourly_rate_cents: z.number().nullable().optional(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: any
}

export function CreateClientDialog({ open, onOpenChange, initialData }: Props) {
  const createClient = useCreateClient()
  const updateClient = useUpdateClient()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      address: "",
      hourly_rate_cents: null,
    }
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        email: initialData.email || "",
        phone: initialData.phone || "",
        address: initialData.address || "",
        hourly_rate_cents: initialData.hourly_rate_cents || null,
      })
    } else {
      reset({
        name: "",
        email: "",
        phone: "",
        address: "",
        hourly_rate_cents: null,
      })
    }
  }, [initialData, reset])

  const isEdit = !!initialData

  const onSubmit = (data: FormValues) => {
    const payload = {
      ...data,
      email: data.email || null,
      phone: data.phone || null,
      address: data.address || null,
      hourly_rate_cents: data.hourly_rate_cents || null,
    }

    if (isEdit) {
      updateClient.mutate({ id: initialData.id, data: payload }, {
        onSuccess: () => {
          toast.success("Client updated")
          onOpenChange(false)
        },
        onError: (err: any) => toast.error(err.response?.data?.detail || "Failed to update client")
      })
    } else {
      createClient.mutate(payload, {
        onSuccess: () => {
          toast.success("Client created")
          onOpenChange(false)
        },
        onError: (err: any) => toast.error(err.response?.data?.detail || "Failed to create client")
      })
    }
  }

  const isPending = createClient.isPending || updateClient.isPending

  return (
    <Dialog open={open} onOpenChange={(val) => {
      onOpenChange(val)
      if (!val) reset()
    }}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Client" : "Add Client"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name <span className="text-red-500">*</span></Label>
            <Input id="name" {...register("name")} placeholder="Client company or full name" />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" type="tel" {...register("phone")} />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="address">Address</Label>
            <Input id="address" {...register("address")} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="hourly_rate">Default Hourly Rate ($)</Label>
            <Input 
              id="hourly_rate" 
              type="number" 
              step="0.01" 
              {...register("hourly_rate_cents", {
                setValueAs: (v) => v === "" || v == null ? null : Math.round(parseFloat(v) * 100)
              })} 
            />
            {errors.hourly_rate_cents && <p className="text-xs text-red-500">{errors.hourly_rate_cents.message}</p>}
          </div>

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending} className="bg-brand-orange hover:bg-brand-orange-hover text-white">
              {isPending ? "Saving..." : isEdit ? "Save Changes" : "Add Client"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
