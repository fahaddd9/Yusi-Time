"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { tokenStore } from "@/lib/token-store"
import { authApi } from "@/features/auth/api"
import { Loader2 } from "lucide-react"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const init = async () => {
      // If no token in memory, try to refresh it using the HttpOnly cookie
      if (!tokenStore.getAccessToken()) {
        try {
          const res = await authApi.refresh()
          tokenStore.setAccessToken(res.data.access_token)
        } catch (error) {
          // If refresh fails (e.g. cookie missing/expired), go to login
          router.push("/login")
          return
        }
      }
      setIsReady(true)
    }
    
    init()
  }, [router])

  if (!isReady) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  // Very minimal shell for now. Phase 4 will implement the full dashboard layout.
  return (
    <main className="min-h-screen bg-background text-foreground">
      {children}
    </main>
  )
}
