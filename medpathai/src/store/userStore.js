import { create } from 'zustand'
import { getUserId } from '../api/auth'

export const useUserStore = create((set, get) => ({
  userId: getUserId(),
  profile: null,
  financials: null,
  documents: [],

  setUserId: (userId) => set({ userId }),
  setProfile: (profile) => set({ profile }),
  setFinancials: (financials) => set({ financials }),
  setDocuments: (documents) => set({ documents }),
  addDocument: (doc) => set((s) => ({ documents: [...s.documents, doc] })),
  clearUser: () => set({ profile: null, financials: null, documents: [] }),

  // Derived
  isProfileComplete: () => !!get().profile,
  hasFinancials: () => !!get().financials,
}))
