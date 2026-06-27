'use client'
/**
 * LogoutGuardDialog — Phase 6.5, Addendum §6.5 (F2).
 *
 * Non-blocking confirmation shown when a Member attempts to log out
 * while their daily hours are below the workspace daily_required_hours target.
 *
 * Copy: "You've logged X.Xh of Yh today. Log out anyway?"
 * Actions: Cancel (keep session) | Log Out Anyway (proceeds)
 *
 * State is managed via attendance-store (openLogoutGuard / closeLogoutGuard).
 * The layout calls openLogoutGuard(hours, onConfirm) instead of immediately
 * calling handleLogout. This dialog calls onConfirm() when the user proceeds.
 *
 * PRD-ADD-03: Guard only activates for Member role — the store openLogoutGuard
 * is only called when role==='member' && attendanceEnabled && below target.
 */

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useAttendanceStore } from '@/stores/attendance-store'

export function LogoutGuardDialog() {
  const { logoutGuardOpen, logoutGuardHours, pendingLogout, closeLogoutGuard } =
    useAttendanceStore()

  const handleConfirm = () => {
    closeLogoutGuard()
    pendingLogout?.()
  }

  const handleCancel = () => {
    closeLogoutGuard()
  }

  return (
    <AlertDialog open={logoutGuardOpen} onOpenChange={(open) => !open && handleCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Log out with hours remaining?</AlertDialogTitle>
          <AlertDialogDescription>
            {logoutGuardHours ? (
              <>
                You&apos;ve logged{' '}
                <span className="font-semibold font-mono">
                  {logoutGuardHours.logged.toFixed(1)}h
                </span>{' '}
                of your{' '}
                <span className="font-semibold font-mono">
                  {logoutGuardHours.required}h
                </span>{' '}
                daily target. Log out anyway?
              </>
            ) : (
              "You haven't reached your daily hour target yet. Log out anyway?"
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel id="logout-guard-cancel" onClick={handleCancel}>
            Stay Logged In
          </AlertDialogCancel>
          <AlertDialogAction
            id="logout-guard-confirm"
            className="bg-destructive text-white hover:bg-destructive/90"
            onClick={handleConfirm}
          >
            Log Out Anyway
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
