"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { tokenStore } from "@/lib/token-store"
import { authApi } from "@/features/auth/api"
import { settingsApi } from "@/features/settings/api"
import { useMe, useWorkspaces, useWorkspace } from "@/features/settings/hooks"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useAttendanceStore } from "@/stores/attendance-store"
import { Sidebar } from "@/features/layout/components/Sidebar"
import { Menu } from "lucide-react"
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"

import { TimerBar } from '@/features/timer/components/TimerBar'
import { IdleModal } from '@/features/timer/components/IdleModal'
import { AttendanceController } from '@/features/attendance/components/AttendanceController'
import { useDailyProgress } from '@/features/attendance/hooks/useAttendance'
import { useBeforeUnloadGuard } from '@/features/attendance/hooks/useBeforeUnloadGuard'
import { useCurrentTimer } from '@/features/time-entries/hooks'

interface WorkspaceMembership {
  workspaceId: string
  workspaceName: string
  role: string
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [isReady, setIsReady] = useState(false)
  const { data: user, refetch: refetchUser } = useMe()
  const { data: workspacesData, refetch: refetchWorkspaces } = useWorkspaces()
  const [membership, setMembership] = useState<WorkspaceMembership | null>(null)
  const { activeWorkspaceId, setWorkspaceId } = useWorkspaceStore()
  const { openLogoutGuard } = useAttendanceStore()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [workspaces, setWorkspaces] = useState<any[]>([])

  // Workspace detail for attendance settings (logout guard)
  const { data: workspaceDetail } = useWorkspace(activeWorkspaceId)

  // Daily progress for logout guard — only fetch for member role when attendance is enabled
  const currentRole = membership?.role ?? 'viewer'
  const attendanceEnabled = workspaceDetail?.attendance_enabled ?? false
  const { data: dailyProgress } = useDailyProgress(
    activeWorkspaceId ?? '',
    currentRole === 'member' && attendanceEnabled
  )

  // Current timer for beforeunload guard
  const { data: currentEntry } = useCurrentTimer(activeWorkspaceId)

  // F2 Case 3: Tab-close beforeunload guard (Addendum §6.6)
  useBeforeUnloadGuard({
    enabled: currentRole === 'member' && attendanceEnabled,
    timerRunning: !!currentEntry,
    hoursLogged: dailyProgress?.hours_logged_today ?? 0,
    dailyRequiredHours: dailyProgress?.daily_required_hours ?? null,
  })

  useEffect(() => {
    if (workspacesData && workspacesData.length > 0) {
      setWorkspaces(workspacesData)
      const targetId = activeWorkspaceId ?? workspacesData[0].id
      const targetWs = workspacesData.find((w: any) => w.id === targetId) ?? workspacesData[0]
      if (membership?.workspaceId !== targetWs.id || membership?.workspaceName !== targetWs.name || membership?.role !== targetWs.role) {
        setWorkspaceId(targetWs.id)
        setMembership({
          workspaceId: targetWs.id,
          workspaceName: targetWs.name,
          role: targetWs.role,
        })
      }
    }
  }, [workspacesData, activeWorkspaceId, setWorkspaceId, membership])

  useEffect(() => {
    const init = async () => {
      let token = tokenStore.getAccessToken()

      if (!token) {
        try {
          const res = await authApi.refresh()
          token = res.data.access_token
          tokenStore.setAccessToken(token as string)
        } catch (error) {
          router.push("/login")
          return
        }
      }

      try {
        const meRes = await settingsApi.getMe()
        if (!meRes.data) throw new Error("Failed to fetch user")
        await refetchUser()
      } catch (error) {
        router.push("/login")
        return
      }

      try {
        // Trigger React Query fetch so workspacesData gets populated
        await refetchWorkspaces()
      } catch {
        // Continue even if workspace fetch fails
      }

      setIsReady(true)
    }

    init()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const doLogout = async () => {
    try {
      await authApi.logout()
    } finally {
      tokenStore.clearAccessToken()
      router.push("/login")
    }
  }

  const handleLogout = () => {
    // F2 — soft-block logout when Member is below daily target (Addendum §2.3, §6.5)
    if (
      currentRole === 'member' &&
      attendanceEnabled &&
      dailyProgress?.daily_required_hours != null &&
      dailyProgress.hours_logged_today < dailyProgress.daily_required_hours
    ) {
      openLogoutGuard(
        { logged: dailyProgress.hours_logged_today, required: dailyProgress.daily_required_hours },
        doLogout
      )
      return
    }
    doLogout()
  }

  const handleWorkspaceChange = (wsId: string) => {
    const targetWs = workspaces.find((w) => w.id === wsId)
    if (targetWs) {
      setWorkspaceId(targetWs.id)
      setMembership({
        workspaceId: targetWs.id,
        workspaceName: targetWs.name,
        role: targetWs.role,
      })
    }
  }

  // Auth Guard: Show full-screen skeleton during in-flight
  if (!isReady) {
    return (
      <div className="flex h-screen overflow-hidden bg-background">
        <div className="hidden md:flex w-14 lg:w-60 bg-[hsl(var(--sidebar-background))] border-r border-sidebar-border p-4 flex-col gap-4">
          <div className="h-8 bg-sidebar-accent rounded w-3/4 mx-auto lg:mx-0 animate-pulse" />
          <div className="h-4 bg-sidebar-accent rounded w-1/2 mt-4 animate-pulse hidden lg:block" />
          <div className="space-y-2 mt-2">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-9 bg-sidebar-accent rounded animate-pulse" />
            ))}
          </div>
        </div>
        <div className="flex flex-col flex-1 min-w-0">
          <div className="h-[52px] border-b border-border bg-card animate-pulse" />
          <div className="p-6 space-y-4">
            <div className="h-8 bg-muted rounded w-1/4 animate-pulse" />
            <div className="h-32 bg-muted rounded animate-pulse" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop Sidebar */}
      {user && (
        <div className="hidden md:flex h-full">
          <Sidebar
            userRole={membership?.role ?? "viewer"}
            userName={user.full_name}
            userEmail={user.email}
            userAvatarUrl={user.avatar_url}
            workspaceName={membership?.workspaceName ?? "Yusi Time"}
            workspaces={workspaces}
            activeWorkspaceId={membership?.workspaceId}
            onWorkspaceChange={handleWorkspaceChange}
            isSuperAdmin={user.is_superadmin}
            onLogout={handleLogout}
            isMobile={false}
          />
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Mobile Header (Hamburger) - visible only on sm */}
        <div className="md:hidden flex items-center p-3 border-b border-border bg-background">
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger
              render={<Button variant="ghost" size="icon" aria-label="Open menu" />}
            >
              <Menu className="w-5 h-5" />
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-60 border-r-sidebar-border" style={{ backgroundColor: 'hsl(var(--sidebar-background))' }}>
              <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
              <SheetDescription className="sr-only">App navigation links</SheetDescription>
              {user && (
                <Sidebar
                  userRole={membership?.role ?? "viewer"}
                  userName={user.full_name}
                  userEmail={user.email}
                  userAvatarUrl={user.avatar_url}
                  workspaceName={membership?.workspaceName ?? "Yusi Time"}
                  workspaces={workspaces}
                  activeWorkspaceId={membership?.workspaceId}
                  onWorkspaceChange={handleWorkspaceChange}
                  isSuperAdmin={user.is_superadmin}
                  onLogout={handleLogout}
                  isMobile={true}
                  onNavClick={() => setMobileMenuOpen(false)}
                />
              )}
            </SheetContent>
          </Sheet>
        </div>

        <TimerBar />
        <main className="flex-1 overflow-y-auto px-6 py-6">
          {children}
        </main>
      </div>
      <IdleModal />
      <AttendanceController />
    </div>
  )
}
