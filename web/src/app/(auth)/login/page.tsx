"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { loginSchema, type LoginInput } from "@/features/auth/schemas"
import { useLogin } from "@/features/auth/hooks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"
import Link from "next/link"
import Image from "next/image"

export default function LoginPage() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) })

  const login = useLogin(setError)

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm p-8 space-y-6">
      {/* Logo mark */}
      <div className="text-center space-y-1">
        <div className="flex justify-center mb-6">
          <Image src="/logo-light.svg" alt="Yusi Time" width={120} height={32} className="dark:hidden" />
          <Image src="/logo-dark.svg" alt="Yusi Time" width={120} height={32} className="hidden dark:block" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Welcome back
        </h1>
        <p className="text-sm text-muted-foreground">
          Sign in to your Yusi Time account
        </p>
      </div>

      {/* Google OAuth button (stub — Phase 1 stretch) */}
      <button
        type="button"
        disabled
        className="w-full flex items-center justify-center gap-2 h-10 px-4 rounded-lg border border-border bg-surface-raised text-sm text-muted-foreground cursor-not-allowed opacity-60"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Continue with Google
      </button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-card px-2 text-muted-foreground tracking-widest">or</span>
        </div>
      </div>

      {/* Email/Password form */}
      <form onSubmit={handleSubmit((data) => login.mutate(data))} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="login-email">Email</Label>
          <Input
            id="login-email"
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
          <div className="flex items-center justify-between">
            <Label htmlFor="login-password">Password</Label>
            <Link
              href="/forgot-password"
              className="text-xs text-brand-orange hover:text-brand-orange-hover transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <Input
            id="login-password"
            type="password"
            placeholder="••••••••"
            autoComplete="current-password"
            {...register("password")}
          />
          {errors.password && (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button
          type="submit"
          disabled={login.isPending}
          className="w-full bg-brand-orange hover:bg-brand-orange-hover text-white font-medium h-10"
        >
          {login.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
          Sign in
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-brand-orange hover:text-brand-orange-hover font-medium transition-colors">
          Sign up free
        </Link>
      </p>
    </div>
  )
}
