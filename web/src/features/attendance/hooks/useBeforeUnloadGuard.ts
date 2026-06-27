/**
 * useBeforeUnloadGuard — Phase 6.5, Addendum §6.6 (F2, Case 3).
 *
 * Attaches a browser `beforeunload` event listener that triggers the native
 * browser confirmation prompt when a Member tries to close/navigate away while:
 *   - A timer is currently running (currentEntry != null)
 *   - Hours today are below daily_required_hours
 *   - Attendance is enabled for the workspace
 *   - User role is 'member'
 *
 * KNOWN LIMITATION (Addendum §8): Modern browsers (Chrome 51+, Firefox, Edge)
 * no longer show the custom string returned by `beforeunload` handlers — they
 * show a generic browser-controlled message. This is a browser anti-abuse
 * restriction and cannot be overridden. The prompt itself still appears, which
 * is the minimum required behavior per the spec. The Addendum explicitly notes
 * this limitation.
 *
 * Called from (app)/layout.tsx. Safe to call unconditionally — internally
 * no-ops when conditions are not met.
 */

import { useEffect } from 'react'

interface UseBeforeUnloadGuardOptions {
  /** Whether the guard should be active at all */
  enabled: boolean
  /** Whether a timer is currently running */
  timerRunning: boolean
  /** Hours logged today */
  hoursLogged: number
  /** Daily required hours target (null = guard disabled) */
  dailyRequiredHours: number | null
}

export function useBeforeUnloadGuard({
  enabled,
  timerRunning,
  hoursLogged,
  dailyRequiredHours,
}: UseBeforeUnloadGuardOptions) {
  const shouldGuard =
    enabled &&
    timerRunning &&
    dailyRequiredHours !== null &&
    hoursLogged < dailyRequiredHours

  useEffect(() => {
    if (!shouldGuard) return

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // Cancelling the event triggers the native browser prompt
      e.preventDefault()
      // Legacy: some browsers use returnValue (ignored visually in modern browsers)
      e.returnValue = ''
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [shouldGuard])
}
