"use client"

import { useMutation } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { authApi } from "../api"
import { tokenStore } from "@/lib/token-store"
import type { UseFormSetError } from "react-hook-form"

// ── useLogin ───────────────────────────────────────────────────────────────

export function useLogin(setError?: UseFormSetError<{ email: string; password: string }>, redirectUrl?: string | null) {
  const router = useRouter()
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => {
      tokenStore.setAccessToken(res.data.access_token)
      router.push(redirectUrl || "/dashboard")
    },
    onError: (err: any) => {
      const code = err?.response?.data?.code
      const detail = err?.response?.data?.detail ?? "An error occurred"
      if (code === "INVALID_CREDENTIALS" && setError) {
        setError("password", { message: "Invalid email or password" })
      } else {
        toast.error(detail)
      }
    },
  })
}

// ── useSignup ──────────────────────────────────────────────────────────────

export function useSignup(setError?: UseFormSetError<{ email: string; password: string; full_name: string; timezone?: string }>, redirectUrl?: string | null) {
  const router = useRouter()
  return useMutation({
    mutationFn: authApi.signup,
    onSuccess: (res) => {
      tokenStore.setAccessToken(res.data.access_token)
      router.push(redirectUrl || "/dashboard")
    },
    onError: (err: any) => {
      const code = err?.response?.data?.code
      const detail = err?.response?.data?.detail ?? "An error occurred"
      if (code === "EMAIL_ALREADY_EXISTS" && setError) {
        setError("email", { message: "An account with this email already exists" })
      } else {
        toast.error(detail)
      }
    },
  })
}

// ── useForgotPassword ──────────────────────────────────────────────────────

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => authApi.forgotPassword(email),
    onError: () => {
      // Always show success message to prevent email enumeration
      // (backend returns 200 regardless, but network errors can still happen)
      toast.error("Something went wrong. Please try again.")
    },
  })
}

// ── useResetPassword ───────────────────────────────────────────────────────

export function useResetPassword() {
  const router = useRouter()
  return useMutation({
    mutationFn: ({ token, new_password }: { token: string; new_password: string }) =>
      authApi.resetPassword(token, new_password),
    onSuccess: () => {
      toast.success("Password reset successfully. Please log in.")
      router.push("/login")
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail ?? "Invalid or expired reset link"
      toast.error(detail)
    },
  })
}

// ── useLogout ──────────────────────────────────────────────────────────────

export function useLogout() {
  const router = useRouter()
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      tokenStore.clearAccessToken()
      router.push("/login")
    },
    onError: () => {
      // Clear token even if server call fails
      tokenStore.clearAccessToken()
      router.push("/login")
    },
  })
}
