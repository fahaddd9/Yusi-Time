/**
 * Idle detector hook — Implementation Plan §4.9 · PRD §3.3.3.
 *
 * Listens for user activity events. When no activity is detected for
 * `timeoutMs` milliseconds, marks the timer as idle via timer-store.
 *
 * On first activity AFTER going idle, opens the idle modal.
 * The modal handles what happens next (keep / discard / continue).
 *
 * Only active when a timer is running AND idle detection is enabled
 * in workspace settings. The parent (TimerBar) decides whether to mount this.
 */
'use client'

import { useEffect, useRef } from 'react'
import { useTimerStore } from '@/stores/timer-store'
import { useUIStore } from '@/stores/ui-store'

const ACTIVITY_EVENTS = [
  'mousemove',
  'mousedown',
  'keydown',
  'touchstart',
  'scroll',
] as const

interface UseIdleDetectorOptions {
  /** Idle timeout in milliseconds (from workspace.idle_timeout_minutes * 60_000) */
  timeoutMs: number
  /** Only run the detector when this is true */
  enabled: boolean
}

export function useIdleDetector({ timeoutMs, enabled }: UseIdleDetectorOptions) {
  const { isIdle, setIdle, clearIdle } = useTimerStore()
  const { openModal } = useUIStore()
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isIdleRef = useRef(isIdle)

  // Keep ref in sync so event handlers see latest value without re-attaching
  useEffect(() => {
    isIdleRef.current = isIdle
  }, [isIdle])

  useEffect(() => {
    if (!enabled) return

    const resetTimer = () => {
      // If we were idle and user moved — open the modal
      // Do NOT clear idle here; the modal owns that decision
      if (isIdleRef.current) {
        openModal('idle')
        return
      }

      // Restart the inactivity countdown
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        // User went idle: record the moment idle was detected
        setIdle(true, new Date())
      }, timeoutMs)
    }

    // Start the initial countdown on mount
    timerRef.current = setTimeout(() => {
      setIdle(true, new Date())
    }, timeoutMs)

    // Attach activity listeners
    ACTIVITY_EVENTS.forEach((event) => {
      window.addEventListener(event, resetTimer, { passive: true })
    })

    return () => {
      // Cleanup on unmount or when enabled/timeoutMs changes
      if (timerRef.current) clearTimeout(timerRef.current)
      ACTIVITY_EVENTS.forEach((event) => {
        window.removeEventListener(event, resetTimer)
      })
      clearIdle()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, timeoutMs])
}
