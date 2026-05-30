"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { resetPasswordSchema, type ResetPasswordInput } from "@/features/auth/schemas"
import { useResetPassword } from "@/features/auth/hooks"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, AlertCircle } from "lucide-react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Suspense } from "react"

function ResetPasswordForm() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordInput>({ resolver: zodResolver(resetPasswordSchema) })

  const resetPassword = useResetPassword()

  if (!token) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm p-8 space-y-6 text-center">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertCircle className="w-6 h-6 text-destructive" />
          </div>
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Invalid link
          </h1>
          <p className="text-sm text-muted-foreground">
            The password reset link is invalid or has expired.
          </p>
        </div>
        <Link href="/forgot-password" className={cn(buttonVariants({ variant: "default" }), "w-full bg-brand-orange hover:bg-brand-orange-hover text-white h-10 mt-6 flex items-center justify-center")}>
          Request new link
        </Link>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm p-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Create new password
        </h1>
        <p className="text-sm text-muted-foreground">
          Your new password must be at least 8 characters long.
        </p>
      </div>

      <form
        onSubmit={handleSubmit((data) => resetPassword.mutate({ token, new_password: data.new_password }))}
        className="space-y-4"
      >
        <div className="space-y-1.5">
          <Label htmlFor="reset-password">New password</Label>
          <Input
            id="reset-password"
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
            {...register("new_password")}
          />
          {errors.new_password && (
            <p className="text-xs text-destructive">{errors.new_password.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirm-password">Confirm new password</Label>
          <Input
            id="confirm-password"
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
            {...register("confirm_password")}
          />
          {errors.confirm_password && (
            <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
          )}
        </div>

        <Button
          type="submit"
          disabled={resetPassword.isPending}
          className="w-full bg-brand-orange hover:bg-brand-orange-hover text-white font-medium h-10"
        >
          {resetPassword.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
          Reset password
        </Button>
      </form>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="bg-card border border-border rounded-xl shadow-sm p-8 flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  )
}
