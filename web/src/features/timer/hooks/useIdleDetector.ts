/**
 * useIdleDetector — Implementation Plan §4.9 + Phase 6.5 F4 (Addendum §2.5).
 *
 * Enhancement strategy (PRD-ADD-07):
 *   1. If `window.IdleDetector` is available (Chrome 94+, Edge 94+) AND
 *      IdleDetector permission is already 'granted', use the native
 *      OS-level idle signal as the detection source.
 *   2. If permission is 'prompt' and we have a user-gesture token
 *      (`requestNativeIdlePermission` was called during handleStart),
 *      request permission then activate native detection.
 *   3. Otherwise (denied / unsupported / Firefox / Safari): fall back to the
 *      existing tab-activity-based detection with zero behavior change.
 *      PRD-ADD-07: "no functional regression for those users."
 *
 * The Idle Modal, its three options, and non-dismissible behavior are
 * COMPLETELY UNCHANGED — only the detection signal source changes (spec §2.5).
 *
 * Permission rules (spec §2.5):
 *   - Permission must be requested in a user gesture (cannot be silent on load)
 *   - Permission must NOT be bundled with push notification permission
 *   - The `requestNativeIdlePermission` helper is exported so TimerBar can call
 *     it inside `handleStart` (which IS a user gesture context)
 */
'use client'

import { useEffect, useRef } from 'react'
import { useTimerStore } from '@/stores/timer-store'
import { useUIStore } from '@/stores/ui-store'

// ── Type augment — IdleDetector is not yet in lib.dom.d.ts for all TS versions ─

declare global {
  interface Window {
    IdleDetector?: {
      requestPermission(): Promise<'granted' | 'denied'>
      new(options?: { threshold: number }): {
        addEventListener(event: 'change', handler: EventListener): void
        removeEventListener(event: 'change', handler: EventListener): void
        start(options?: { threshold: number; signal?: AbortSignal }): Promise<void>
        readonly userState: 'active' | 'idle'
        readonly screenState: 'locked' | 'unlocked'
      }
    }
  }
}

// ── Activity events for fallback detection ────────────────────────────────────

const ACTIVITY_EVENTS = [
  'mousemove',
  'mousedown',
  'keydown',
  'touchstart',
  'scroll',
] as const

// ── Public helper — call inside a user gesture handler (e.g. handleStart) ─────

/**
 * Requests IdleDetector permission if the API is available and not yet granted.
 * Must be called inside a user-gesture handler (click, keydown, etc.).
 * Returns the resulting permission state, or 'unsupported' if unavailable.
 *
 * PRD-ADD-07 / Addendum §2.5: Do NOT bundle with push notification permission.
 */
export async function requestNativeIdlePermission(): Promise<
  'granted' | 'denied' | 'unsupported'
> {
  if (!window.IdleDetector) return 'unsupported'
  try {
    const result = await window.IdleDetector.requestPermission()
    return result
  } catch {
    return 'denied'
  }
}

// ── Hook ──────────────────────────────────────────────────────────────────────

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
  const abortRef = useRef<AbortController | null>(null)

  // Keep ref in sync so event handlers see latest value without re-attaching
  useEffect(() => {
    isIdleRef.current = isIdle
  }, [isIdle])

  useEffect(() => {
    if (!enabled) return

    // ── Shared: the action to take when idle is confirmed ───────────────────
    const onIdleDetected = () => {
      if (!isIdleRef.current) {
        setIdle(true, new Date())
      }
    }

    // ── Shared: the action to take when activity resumes ───────────────────
    const onActivityDetected = () => {
      if (isIdleRef.current) {
        openModal('idle')
      }
    }

    // ── Try native IdleDetector (F4 enhancement) ────────────────────────────
    const tryNativeDetector = async () => {
      const pref = typeof window !== 'undefined' && localStorage.getItem('os_idle_preference') === 'enabled'
      if (!pref) return false // User disabled OS-level idle detection

      if (!window.IdleDetector) return false // Not supported — use fallback

      try {
        // Check current permission without a fresh request (no user gesture needed)
        // We rely on the fact that requestNativeIdlePermission() was already called
        // by the user gesture in TimerBar.handleStart. If it wasn't called or was
        // denied, this will throw and we fall back.
        //
        // Implementation: attempt to start the detector. If permission was not
        // granted, start() will throw a DOMException with name 'NotAllowedError'.

        const controller = new AbortController()
        abortRef.current = controller

        // @ts-ignore — IdleDetector constructor
        const detector = new window.IdleDetector()

        let nativeStarted = false

        await detector.start({
          threshold: Math.max(timeoutMs, 60000), // API spec requires at least 1 minute
          signal: controller.signal,
        })

        nativeStarted = true

        detector.addEventListener('change', () => {
          const userIdle = detector.userState === 'idle'
          const screenLocked = detector.screenState === 'locked'

          if (userIdle || screenLocked) {
            onIdleDetected()
          } else {
            // User became active again — trigger modal if we were idle
            onActivityDetected()
          }
        })

        return nativeStarted
      } catch (e: any) {
        // NotAllowedError = permission not granted → fall back
        // AbortError = cleanup → ignore
        if (e?.name === 'AbortError') return true // cleanup, not a real error
        console.warn("Native IdleDetector failed to start, falling back:", e)
        return false
      }
    }

    // ── Fallback: existing tab-activity-based detection ────────────────────
    const startFallbackDetection = () => {
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

      // Return cleanup
      return () => {
        if (timerRef.current) clearTimeout(timerRef.current)
        ACTIVITY_EVENTS.forEach((event) => {
          window.removeEventListener(event, resetTimer)
        })
      }
    }

    // ── Orchestrate: try native, fall back if unavailable/denied ───────────
    let fallbackCleanup: (() => void) | undefined

    tryNativeDetector().then((nativeActive) => {
      if (!nativeActive) {
        // Native unavailable or denied — use existing behavior (zero regression)
        fallbackCleanup = startFallbackDetection()
      }
      // If nativeActive=true, the AbortController handles cleanup
    })

    return () => {
      // Cleanup AbortController (stops native detector)
      if (abortRef.current) {
        abortRef.current.abort()
        abortRef.current = null
      }
      // Cleanup fallback timers/listeners
      fallbackCleanup?.()
      clearIdle()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, timeoutMs])
}
