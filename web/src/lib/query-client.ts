/**
 * Singleton QueryClient — must be created once and shared across the app.
 *
 * getQueryClient() is safe to call from outside React components (e.g. Zustand stores).
 * The QueryClientWrapper in the component tree uses this same instance.
 *
 * Blueprint v2.0 · Phase 2 Step 2.8.
 */
import { QueryClient } from '@tanstack/react-query'

let queryClientInstance: QueryClient | null = null

export function getQueryClient(): QueryClient {
  if (!queryClientInstance) {
    queryClientInstance = new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 30 * 1000, // 30 seconds — short enough to pick up mutations quickly
          retry: 1,
          refetchOnWindowFocus: true, // Auto-refetch stale queries on tab/window focus
        },
      },
    })
  }
  return queryClientInstance
}
