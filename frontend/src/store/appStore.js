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
  // Logbook/Report state
  selectedLogbookEntryId: null,
  selectedReportId: null,
  // Role-based access
  userRole: null, // 'engineer' | 'manager' | 'technician' | 'judge'

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
  // Logbook/Report actions
  openLogbookEntry: (entryId) =>
    set({ selectedLogbookEntryId: entryId, activePanel: 'logbook' }),
  openReport: (reportId) =>
    set({ selectedReportId: reportId, activePanel: 'reports' }),
  clearLogbookSelection: () => set({ selectedLogbookEntryId: null }),
  clearReportSelection: () => set({ selectedReportId: null }),
  // Role actions
  setUserRole: (role) => {
    localStorage.setItem('userRole', role)
    set({ userRole: role })
  },
  loadUserRole: () => {
    const role = localStorage.getItem('userRole')
    set({ userRole: role })
  },
}))

export default useAppStore
