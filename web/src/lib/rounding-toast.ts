/**
 * Rounding toast — Implementation Plan §4.11 · PRD §7.
 *
 * Called in EVERY mutation onSuccess that saves a time entry.
 * This is NON-NEGOTIABLE per the Phase 4 testing checklist.
 *
 * Shows:
 *   - When rounding occurred: "Saved as 1h 15m" + description showing raw → rounded
 *   - When no rounding: "Saved: 1h 3m" (plain confirmation)
 */
import { toast } from 'sonner'
import { formatDuration } from './utils'

export interface RoundingResult {
  raw_seconds: number
  rounded_seconds: number
  rounding_mode: string
  rounding_interval_minutes: number | null
}

export function showRoundingToast(rounding: RoundingResult): void {
  const wasRounded = rounding.raw_seconds !== rounding.rounded_seconds
  const rounded = formatDuration(rounding.rounded_seconds)
  const raw = formatDuration(rounding.raw_seconds)

  if (wasRounded) {
    toast.success(`Saved as ${rounded}`, {
      description: `${raw} → rounded ${rounding.rounding_mode} to nearest ${rounding.rounding_interval_minutes}m`,
      duration: 5000,
    })
  } else {
    toast.success(`Saved: ${rounded}`, { duration: 3000 })
  }
}
