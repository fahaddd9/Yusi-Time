"use client"

import { QueryClientProvider } from '@tanstack/react-query'
import { getQueryClient } from '@/lib/query-client'

export function QueryClientWrapper({ children }: { children: React.ReactNode }) {
  // Use the singleton from lib/query-client so Zustand stores can call getQueryClient().clear()
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
