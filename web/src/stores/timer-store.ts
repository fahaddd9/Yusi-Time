/**
 * Timer store — tracks idle detection state for the running timer.
 * Implementation Plan §4.8 · PRD §3.3.3 Idle Detection.
 *
 * isIdle:      true when the user has been inactive beyond the workspace timeout
 * idleStartTime: the moment idle was detected (used by the Idle Modal to compute
 *               the idle_end_time sent to the stop endpoint)
 *
 * The store intentionally holds ONLY idle state — elapsed seconds are computed
 * live from start_time in the TimerBar to avoid re-render loops.
 */
import { create } from 'zustand'

interface TimerStore {
  isIdle: boolean
  idleStartTime: Date | null
  setIdle: (isIdle: boolean, idleStartTime: Date | null) => void
  clearIdle: () => void
}

export const useTimerStore = create<TimerStore>((set) => ({
  isIdle: false,
  idleStartTime: null,

  setIdle: (isIdle, idleStartTime) => set({ isIdle, idleStartTime }),

  clearIdle: () => set({ isIdle: false, idleStartTime: null }),
}))
