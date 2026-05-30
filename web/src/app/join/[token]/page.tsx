"use client"

import { useQuery, useMutation } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react"
import Link from "next/link"
import { ThemeToggle } from "@/components/ThemeToggle"
import { useRouter } from "next/navigation"

export default function JoinWorkspacePage({ params }: { params: { token: string } }) {
  const router = useRouter()
  const { token } = params

  const { data, isLoading, error, isError } = useQuery({
    queryKey: ["invite", token],
    queryFn: () => apiClient.get(`/invites/${token}`).then(res => res.data),
    retry: false,
  })

  // Accept invite mutation
  const acceptInvite = useMutation({
    mutationFn: () => apiClient.post(`/invites/${token}/accept`),
    onSuccess: () => {
      // Refresh user/workspaces on next load, then go to dashboard
      router.push("/dashboard")
    },
  })

  let content

  if (isLoading) {
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
        <Link href="/login" className={cn(buttonVariants({ variant: "default" }), "w-full bg-brand-navy hover:bg-brand-navy/90 text-white h-10 mt-6 flex items-center justify-center")}>
          Go to login
        </Link>
      </div>
    )
  } else {
    // Valid invite
    const invite = data?.data
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
            className="w-full bg-brand-orange hover:bg-brand-orange-hover text-white font-medium h-10"
          >
            {acceptInvite.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
            Accept Invitation
          </Button>
          <p className="text-xs text-muted-foreground">
            If you don&apos;t have an account yet, you will be prompted to create one.
          </p>
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
