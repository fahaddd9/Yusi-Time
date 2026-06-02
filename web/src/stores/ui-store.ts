/**
 * UI store — global UI state (sidebar, active modal).
 *
 * Blueprint v2.0 G2 · IMPLEMENTATION_PLAN Phase 2 Step 2.8.
 */
import { create } from 'zustand'

interface UIStore {
  sidebarOpen: boolean
  activeModal: string | null
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  openModal: (id: string) => void
  closeModal: () => void
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  activeModal: null,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
}))
