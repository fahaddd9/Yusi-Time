import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60

  if (h > 0) {
    if (m === 0) return `${h}h`
    return `${h}h ${m}m`
  }
  
  if (m > 0) {
    if (s === 0) return `${m}m`
    return `${m}m ${s}s`
  }
  
  return `${s}s`
}

export function formatMoney(cents: number | null | undefined): string {
  if (cents == null) return '—'
  return `$${(cents / 100).toFixed(2)}`
}

export function descriptionDraftKey(userId: string, workspaceId: string): string {
  return `yt_desc_draft_${userId}_${workspaceId}`
}
