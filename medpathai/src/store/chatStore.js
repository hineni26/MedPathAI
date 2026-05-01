import { create } from 'zustand'

export const useChatStore = create((set) => ({
  sessionId: null,
  messages: [],          // { id, role: 'user'|'ai', content, data?, timestamp }
  selectedHospital: null,
  isLoading: false,

  setSessionId: (id) => set({ sessionId: id }),
  setLoading: (v) => set({ isLoading: v }),
  setSelectedHospital: (h) => set({ selectedHospital: h }),

  addMessage: (msg) =>
    set((s) => ({
      messages: [...s.messages, { id: Date.now(), timestamp: new Date(), ...msg }],
    })),

  updateLastAIMessage: (data) =>
    set((s) => {
      const msgs = [...s.messages]
      const lastAI = [...msgs].reverse().find((m) => m.role === 'ai')
      if (lastAI) lastAI.data = data
      return { messages: msgs }
    }),

  clearChat: () =>
    set({ messages: [], sessionId: null, selectedHospital: null }),
}))
