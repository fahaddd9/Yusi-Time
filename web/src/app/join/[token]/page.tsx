"use client"
import { useState, useEffect } from "react"

import { useQuery, useMutation } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import { authApi } from "@/features/auth/api"
import { tokenStore } from "@/lib/token-store"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react"
import Link from "next/link"
import { ThemeToggle } from "@/components/ThemeToggle"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

export default function JoinWorkspacePage({ params }: { params: { token: string } }) {
  const router = useRouter()
  const { token } = params

  // Three-state auth check:
  //   'checking'     — doing a silent refresh to see if the user is actually logged in
  //   'authenticated' — confirmed logged in (token refreshed or already in memory)
  //   'unauthenticated' — refresh failed; user must log in first
  const [authState, setAuthState] = useState<'checking' | 'authenticated' | 'unauthenticated'>('checking')

  useEffect(() => {
    // If the in-memory token is already set (e.g. user navigated within the SPA), we're done.
    if (tokenStore.getAccessToken()) {
      setAuthState('authenticated')
      return
    }

    // The token isn't in memory yet. This happens on a cold page load (e.g. pasting
    // an invite link while logged in). Attempt a silent refresh using the HttpOnly
    // refresh_token cookie before deciding the user is logged out.
    authApi.refresh()
      .then((res) => {
        tokenStore.setAccessToken(res.data.access_token)
        setAuthState('authenticated')
      })
      .catch(() => {
        // Refresh failed — user is genuinely not logged in. Send them to login
        // with the invite URL as the redirect param so they land back here after.
        router.push(`/login?redirect=/join/${token}`)
        setAuthState('unauthenticated')
      })
  }, [token, router])

  const { data, isLoading, error, isError } = useQuery({
    queryKey: ["invite", token],
    queryFn: () => apiClient.get(`/invites/${token}`).then((res) => res.data),
    // Only fire the query once we've confirmed the user is authenticated.
    enabled: authState === 'authenticated',
    retry: false,
  })

  // Accept invite mutation
  const acceptInvite = useMutation({
    mutationFn: () => apiClient.post(`/invites/${token}/accept`),
    onSuccess: () => {
      toast.success("You've joined the workspace!")
      // Go to dashboard. AppLayout will refresh user/workspaces automatically.
      router.push("/dashboard")
    },
    onError: (error: any) => {
      if (error.response?.status === 401) {
        router.push(`/login?redirect=/join/${token}`)
      } else if (error.response?.data?.code === 'ALREADY_MEMBER') {
        toast.info("You're already a member of this workspace.")
        router.push("/dashboard")
      } else {
        const msg = error.response?.data?.detail || "Failed to accept invite"
        toast.error(msg)
      }
    }
  })

  let content

  // Show a spinner while we're doing the silent refresh check
  if (authState === 'checking' || authState === 'unauthenticated') {
    content = (
      <div className="flex justify-center items-center h-40">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  } else if (isLoading) {
    content = (
      <div className="flex justify-center items-center h-40">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  } else if (isError) {
    const errCode = (error as any)?.response?.data?.code
    const errDetail = (error as any)?.response?.data?.detail || "Invalid or expired invite link."

    content = (
      <div className="text-center space-y-6">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertCircle className="w-6 h-6 text-destructive" />
          </div>
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            {errCode === "INVITE_EXPIRED"
              ? "Invite Expired"
              : errCode === "INVITE_USED"
              ? "Invite Already Used"
              : "Invalid Invite"}
          </h1>
          <p className="text-sm text-muted-foreground">{errDetail}</p>
        </div>
        <Link href="/dashboard" className={cn(buttonVariants({ variant: "default" }), "w-full bg-brand-navy hover:bg-brand-navy/90 text-white h-10 mt-6 flex items-center justify-center")}>
          Go to Dashboard
        </Link>
      </div>
    )
  } else {
    // Valid invite — show the Accept button
    const invite = data
    content = (
      <div className="text-center space-y-6">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-brand-orange/10 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6 text-brand-orange" />
          </div>
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            You&apos;ve been invited!
          </h1>
          <p className="text-sm text-muted-foreground">
            You have been invited to join <strong>{invite?.workspace_name}</strong>{" "}
            as a <strong>{invite?.role}</strong>.
          </p>
        </div>
        <div className="pt-4 space-y-3">
          <Button
            onClick={() => acceptInvite.mutate()}
            disabled={acceptInvite.isPending}
            className="w-full bg-primary hover:bg-primary/90 text-white shadow-[0_0_15px_rgba(254,105,0,0.3)] font-medium h-10"
          >
            {acceptInvite.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Accept Invitation
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background styling matching AuthLayout */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage: "radial-gradient(circle, hsl(var(--foreground)) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />
      <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full bg-brand-orange/5 blur-[80px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[300px] h-[300px] rounded-full bg-brand-navy/10 blur-[80px] pointer-events-none dark:bg-brand-orange/5" />
      
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      <div className="relative z-10 w-full max-w-[420px]">
        <div className="bg-card border border-border rounded-xl shadow-sm p-8">
          {content}
        </div>
      </div>
    </div>
  )
}
