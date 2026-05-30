"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { signupSchema, type SignupInput } from "@/features/auth/schemas"
import { useSignup } from "@/features/auth/hooks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"
import Link from "next/link"
import { useState } from "react"

function PasswordStrengthBar({ password }: { password: string }) {
  const strength = !password
    ? 0
    : password.length >= 12 && /[A-Z]/.test(password) && /[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)
    ? 3
    : password.length >= 8 && (/[A-Z]/.test(password) || /[0-9]/.test(password))
    ? 2
    : 1

  const colors = ["", "bg-destructive", "bg-warning", "bg-success"]
  const labels = ["", "Weak", "Fair", "Strong"]

  if (!password) return null
  return (
    <div className="space-y-1">
      <div className="flex gap-1">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
              i <= strength ? colors[strength] : "bg-muted"
            }`}
          />
        ))}
      </div>
      <p className={`text-xs ${strength === 1 ? "text-destructive" : strength === 2 ? "text-warning" : "text-success"}`}>
        {labels[strength]}
      </p>
    </div>
  )
}

export default function SignupPage() {
  const [password, setPassword] = useState("")

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<SignupInput>({ resolver: zodResolver(signupSchema) })

  const signup = useSignup(setError)

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm p-8 space-y-6">
      <div className="text-center space-y-1">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-brand-orange mb-3">
          <span className="text-white font-bold text-lg font-mono">Y</span>
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Create your account
        </h1>
        <p className="text-sm text-muted-foreground">
          Start tracking time in under a minute
        </p>
      </div>

      <form onSubmit={handleSubmit((data) => signup.mutate(data))} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="signup-name">Full name</Label>
          <Input
            id="signup-name"
            type="text"
            placeholder="Alex Johnson"
            autoComplete="name"
            {...register("full_name")}
          />
          {errors.full_name && (
            <p className="text-xs text-destructive">{errors.full_name.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="signup-email">Email</Label>
          <Input
            id="signup-email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="signup-password">Password</Label>
          <Input
            id="signup-password"
            type="password"
            placeholder="Min. 8 characters"
            autoComplete="new-password"
            {...register("password", {
              onChange: (e) => setPassword(e.target.value),
            })}
          />
          <PasswordStrengthBar password={password} />
          {errors.password && (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button
          type="submit"
          disabled={signup.isPending}
          className="w-full bg-brand-orange hover:bg-brand-orange-hover text-white font-medium h-10"
        >
          {signup.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
          Create account
        </Button>
      </form>

      <p className="text-center text-xs text-muted-foreground">
        By signing up you agree to our{" "}
        <span className="text-foreground">Terms of Service</span> and{" "}
        <span className="text-foreground">Privacy Policy</span>.
      </p>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="text-brand-orange hover:text-brand-orange-hover font-medium transition-colors">
          Sign in
        </Link>
      </p>
    </div>
  )
}
