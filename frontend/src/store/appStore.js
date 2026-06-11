import { create } from 'zustand'

const useAppStore = create((set) => ({
  // 'chat' | 'monitor' | 'documents' | 'reports' | 'logbook' | 'equipment'
  activePanel: 'chat',
  selectedEquipmentTag: null,
  alertCount: 0,
  activeCitation: null,
  isPDFViewerOpen: false,
  // Live Monitor — persistent chat drawer
  isMonitorChatOpen: false,
  // Documents state
  documents: [],
  selectedDocumentId: null,

  setActivePanel: (panel) => set({ activePanel: panel }),
  setSelectedTag: (tag) => set({ selectedEquipmentTag: tag }),
  setActiveCitation: (citation) =>
    set({ activeCitation: citation, isPDFViewerOpen: true }),
  closePDFViewer: () =>
    set({ isPDFViewerOpen: false, activeCitation: null }),
  incrementAlerts: () =>
    set((s) => ({ alertCount: s.alertCount + 1 })),
  resetAlerts: () => set({ alertCount: 0 }),
  toggleMonitorChat: () =>
    set((s) => ({ isMonitorChatOpen: !s.isMonitorChatOpen })),
  openMonitorChat: () => set({ isMonitorChatOpen: true }),
  // Document actions
  setDocuments: (documents) => set({ documents }),
  openDocument: (docId) =>
    set({ selectedDocumentId: docId, activePanel: 'documents', isPDFViewerOpen: true }),
}))

export default useAppStore
