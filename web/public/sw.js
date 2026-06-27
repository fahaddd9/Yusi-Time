/**
 * Yusi Time — Web Push Service Worker
 * Phase 6.5, Addendum §5.3, §6.8.
 *
 * Handles push events from the backend (pywebpush) and displays OS-level
 * notifications. On notification click, focuses the app or opens a new tab.
 *
 * Registration: performed in usePushNotifications hook on first user gesture.
 * This file is served from /sw.js by Next.js static file serving (web/public/).
 *
 * Push payload format sent by the backend (JSON):
 *   {
 *     "title": string,
 *     "body":  string,
 *     "icon":  string (optional, defaults to /icon-192.png),
 *     "tag":   string (optional, deduplicates notifications with same tag),
 *     "url":   string (optional, route to open on click, e.g. "/dashboard")
 *   }
 *
 * Limitation note (Addendum §8): push only works on HTTPS and localhost.
 * HTTP deployments will silently fail at ServiceWorkerRegistration.pushManager.subscribe().
 */

/* eslint-disable no-restricted-globals */

const APP_ORIGIN = self.location.origin

// ── Push event handler ────────────────────────────────────────────────────────

self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data ? event.data.json() : {}
  } catch {
    // Malformed payload — show a generic notification
    data = { title: 'Yusi Time', body: 'You have a new notification.' }
  }

  const title = data.title ?? 'Yusi Time'
  const options = {
    body: data.body ?? '',
    icon: data.icon ?? '/icon-192.png',
    badge: '/icon-96.png',
    tag: data.tag ?? 'yusi-time-default',
    // Store the target URL in notification data for click handler
    data: { url: data.url ?? '/' },
    // Vibrate pattern for mobile (ignored on desktop)
    vibrate: [100, 50, 100],
    // Close other notifications with the same tag (deduplication)
    renotify: !!data.tag,
  }

  event.waitUntil(
    self.registration.showNotification(title, options)
  )
})

// ── Notification click handler ────────────────────────────────────────────────

self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  const targetUrl = event.notification.data?.url
    ? `${APP_ORIGIN}${event.notification.data.url}`
    : APP_ORIGIN

  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Try to focus an existing tab showing our app
        for (const client of clientList) {
          if (client.url.startsWith(APP_ORIGIN) && 'focus' in client) {
            client.navigate(targetUrl)
            return client.focus()
          }
        }
        // No existing tab — open a new one
        if (self.clients.openWindow) {
          return self.clients.openWindow(targetUrl)
        }
      })
  )
})

// ── Install + Activate (minimal — no offline caching) ─────────────────────────

self.addEventListener('install', () => {
  // Skip waiting so new SW activates immediately
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  // Claim all clients so push notifications work on first install
  event.waitUntil(self.clients.claim())
})
