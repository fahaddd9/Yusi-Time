/**
 * Description draft hook — Implementation Plan §4.10 · PRD §3.3.2.
 *
 * Persists the timer description input to localStorage so it survives
 * page reloads. Cleared automatically on start/stop.
 *
 * Key format: `yt_desc_draft_{userId}_{workspaceId}`
 * This prevents cross-user/cross-workspace draft leakage.
 */
'use client'

import { useCallback, useEffect, useRef } from 'react'

const DRAFT_DEBOUNCE_MS = 500

function buildKey(userId: string, workspaceId: string): string {
  return `yt_desc_draft_${userId}_${workspaceId}`
}

interface UseDescriptionDraftOptions {
  userId: string
  workspaceId: string
}

interface UseDescriptionDraftReturn {
  getDraft: () => string
  saveDraft: (value: string) => void
  clearDraft: () => void
}

export function useDescriptionDraft({
  userId,
  workspaceId,
}: UseDescriptionDraftOptions): UseDescriptionDraftReturn {
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const key = buildKey(userId, workspaceId)

  const getDraft = useCallback((): string => {
    // SSR guard — localStorage is browser-only
    if (typeof window === 'undefined') return ''
    return localStorage.getItem(key) ?? ''
  }, [key])

  const saveDraft = useCallback(
    (value: string) => {
      if (typeof window === 'undefined') return
      // Cancel any pending debounced save
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => {
        if (value.trim() === '') {
          localStorage.removeItem(key)
        } else {
          localStorage.setItem(key, value)
        }
      }, DRAFT_DEBOUNCE_MS)
    },
    [key],
  )

  const clearDraft = useCallback(() => {
    if (typeof window === 'undefined') return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    localStorage.removeItem(key)
  }, [key])

  // Clear any pending debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  return { getDraft, saveDraft, clearDraft }
}
