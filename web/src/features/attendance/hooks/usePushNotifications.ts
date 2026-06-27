/**
 * usePushNotifications — Phase 6.5, Addendum §6.8.
 *
 * Orchestrates the full Web Push subscription lifecycle:
 *   1. Detect current browser permission state (granted/denied/default)
 *   2. Register the service worker (/sw.js)
 *   3. Request Notification.requestPermission() on user gesture
 *   4. Subscribe via PushManager.subscribe() with the VAPID public key
 *   5. POST the subscription to backend via attendanceApi.registerPushSubscription
 *   6. On toggle OFF: DELETE the subscription from backend + unsubscribe PushManager
 *
 * Critical (Addendum §6.8 browser permission rules):
 *   - NEVER auto-request permission on page load
 *   - MUST be triggered by a direct user gesture (toggle click)
 *   - The permission prompt and push subscription are separate from IdleDetector
 *     permission (§2.5) — unrelated browser permissions, must not be bundled
 *
 * VAPID_PUBLIC_KEY must be set as NEXT_PUBLIC_VAPID_PUBLIC_KEY in .env.local.
 * Without it, subscribe() will fail gracefully and the toggle returns to OFF.
 *
 * Limitations:
 *   - Only works on HTTPS and localhost (browser enforcement)
 *   - Not supported in Firefox Private Browsing, iOS Safari < 16.4
 *   - If the user denies the permission prompt, the toggle resets to OFF and
 *     shows a "Permission denied" status
 */

'use client'

import { useState, useEffect, useCallback } from 'react'
import { usePushSubscription } from './useAttendance'

// ── Types ─────────────────────────────────────────────────────────────────────

export type PushPermissionState = 'unsupported' | 'denied' | 'default' | 'granted'

export interface UsePushNotificationsResult {
  /** Whether push is fully active (permission granted + subscribed) */
  isEnabled: boolean
  /** Current browser permission state */
  permissionState: PushPermissionState
  /** True while permission request or subscription is in flight */
  isPending: boolean
  /** Human-readable status for display in settings UI */
  statusLabel: string
  /** Call on toggle ON — must be called from a user gesture handler */
  enable: () => Promise<void>
  /** Call on toggle OFF */
  disable: () => Promise<void>
}

// ── VAPID key helper ──────────────────────────────────────────────────────────

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function usePushNotifications(): UsePushNotificationsResult {
  const { register, unregister } = usePushSubscription()
  const [permissionState, setPermissionState] = useState<PushPermissionState>('default')
  const [isEnabled, setIsEnabled] = useState(false)
  const [isPending, setIsPending] = useState(false)
  const [backendSubId, setBackendSubId] = useState<string | null>(null)

  // Detect initial permission state on mount (no user gesture needed for query)
  useEffect(() => {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) {
      setPermissionState('unsupported')
      return
    }
    const perm = Notification.permission
    setPermissionState(perm === 'granted' ? 'granted' : perm === 'denied' ? 'denied' : 'default')

    // Check if already subscribed
    if (perm === 'granted') {
      navigator.serviceWorker.ready.then((reg) => {
        reg.pushManager.getSubscription().then((sub) => {
          if (sub) setIsEnabled(true)
        })
      }).catch(() => {})
    }
  }, [])

  const enable = useCallback(async () => {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) {
      setPermissionState('unsupported')
      return
    }
    setIsPending(true)
    try {
      // Step 1: Register service worker
      const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' })

      // Step 2: Request permission (user gesture context — called from toggle click)
      const permission = await Notification.requestPermission()
      setPermissionState(permission === 'granted' ? 'granted' : permission === 'denied' ? 'denied' : 'default')

      if (permission !== 'granted') {
        return // User denied — leave toggle OFF, show denied state
      }

      // Step 3: Subscribe via PushManager
      const vapidKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY
      if (!vapidKey) {
        console.warn('[PushNotifications] NEXT_PUBLIC_VAPID_PUBLIC_KEY not set — cannot subscribe')
        return
      }

      const subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey) as unknown as BufferSource,
      })

      const subJson = subscription.toJSON()
      const p256dhKey = subJson.keys?.p256dh ?? ''
      const authKey = subJson.keys?.auth ?? ''

      // Step 4: POST to backend
      const result = await register.mutateAsync({
        endpoint: subscription.endpoint,
        p256dh_key: p256dhKey,
        auth_key: authKey,
      })

      setBackendSubId(result.data.id)
      setIsEnabled(true)
    } catch (err) {
      console.error('[PushNotifications] enable failed:', err)
    } finally {
      setIsPending(false)
    }
  }, [register])

  const disable = useCallback(async () => {
    setIsPending(true)
    try {
      // Unsubscribe from PushManager
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      if (sub) await sub.unsubscribe()

      // DELETE from backend if we have the subscription ID
      if (backendSubId) {
        await unregister.mutateAsync(backendSubId)
        setBackendSubId(null)
      }

      setIsEnabled(false)
    } catch (err) {
      console.error('[PushNotifications] disable failed:', err)
    } finally {
      setIsPending(false)
    }
  }, [unregister, backendSubId])

  const statusLabel: string = (() => {
    if (permissionState === 'unsupported') return 'Not supported in this browser'
    if (permissionState === 'denied') return 'Permission denied — enable in browser settings'
    if (isPending) return 'Requesting permission…'
    if (isEnabled) return ''
    return ''
  })()

  return {
    isEnabled,
    permissionState,
    isPending,
    statusLabel,
    enable,
    disable,
  }
}
