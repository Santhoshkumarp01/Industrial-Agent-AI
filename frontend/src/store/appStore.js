import { create } from 'zustand'

const useAppStore = create((set) => ({
  activePanel: 'chat',        // 'chat' | 'monitor' | 'documents' | 'reports'
  selectedEquipmentTag: null, // filter for chat queries
  alertCount: 0,
  activeCitation: null,       // { docId, page, bbox, docName }
  isPDFViewerOpen: false,

  setActivePanel: (panel) => set({ activePanel: panel }),
  setSelectedTag: (tag) => set({ selectedEquipmentTag: tag }),
  setActiveCitation: (citation) =>
    set({ activeCitation: citation, isPDFViewerOpen: true }),
  closePDFViewer: () =>
    set({ isPDFViewerOpen: false, activeCitation: null }),
  incrementAlerts: () =>
    set((s) => ({ alertCount: s.alertCount + 1 })),
  resetAlerts: () => set({ alertCount: 0 }),
}))

export default useAppStore
