import { create } from 'zustand'

const THEME_KEY = 'medpath_theme'

function getInitialTheme() {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved === 'dark' || saved === 'light') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useUIStore = create((set, get) => ({
  providerMode: false,
  theme: getInitialTheme(),
  toasts: [],
  modal: null,   // { type, props }

  setProviderMode: (v) => set({ providerMode: v }),
  setTheme: (theme) => {
    localStorage.setItem(THEME_KEY, theme)
    set({ theme })
  },
  toggleTheme: () => {
    const theme = get().theme === 'dark' ? 'light' : 'dark'
    localStorage.setItem(THEME_KEY, theme)
    set({ theme })
  },
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
