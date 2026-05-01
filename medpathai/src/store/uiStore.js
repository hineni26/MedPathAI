import { create } from 'zustand'

export const useUIStore = create((set) => ({
  providerMode: false,
  toasts: [],
  modal: null,   // { type, props }

  setProviderMode: (v) => set({ providerMode: v }),
  openModal: (type, props = {}) => set({ modal: { type, props } }),
  closeModal: () => set({ modal: null }),

  toast: (message, type = 'info', duration = 4000) => {
    const id = Date.now()
    set((s) => ({ toasts: [...s.toasts, { id, message, type }] }))
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
    }, duration)
  },

  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
