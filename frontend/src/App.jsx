import React, { useEffect, useCallback, useState } from 'react'
import Layout from './components/layout/Layout'
import ChatPanel from './components/chat/ChatPanel'
import MonitoringPanel from './components/monitoring/MonitoringPanel'
import ReportsPanel from './components/monitoring/ReportsPanel'
import LogbookPanel from './components/monitoring/LogbookPanel'
import { useChat } from './hooks/useChat'
import { useSensorStream } from './hooks/useSensorStream'
import { useDocuments } from './hooks/useDocuments'
import useAppStore from './store/appStore'

export default function App() {
  const activePanel = useAppStore((s) => s.activePanel)
  const setActivePanel = useAppStore((s) => s.setActivePanel)

  // ── Separate chat histories ──────────────────────────────────────────────
  // chatHook       → Chat Assistant panel (document-intelligence)
  // monitorChatHook → Live Monitor Intelligence panel (machine analysis)
  const chatHook = useChat()
  const monitorChatHook = useChat({ isMonitor: true })

  const documentsHook = useDocuments()

  const handleAlertDetected = useCallback(() => {}, [])
  const sensorHook = useSensorStream(handleAlertDetected)

  // Ctrl+Shift+D — inject anomaly + auto-run analysis in Monitor chat
  useEffect(() => {
    const handleKeyDown = async (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault()
        const machineTag = 'rolling-mill-main-drive-motor'

        // Trigger frontend simulator anomaly
        sensorHook.triggerAnomaly(machineTag, 'vibration')

        try {
          const { injectMachineAnomaly, runMachineAnalysis } = await import('./services/api')
          await injectMachineAnomaly(machineTag)

          // Auto-analyze after 3 seconds with notification in monitor chat
          setTimeout(async () => {
            if (monitorChatHook?.addAnalyzingMessage) {
              monitorChatHook.addAnalyzingMessage('⚡ Anomaly detected — Analyzing Rolling Mill Main Drive Motor...')
            }
            // Switch to monitor panel
            setActivePanel('monitor')
            try {
              const result = await runMachineAnalysis(machineTag, { includeLogs: 10 })
              if (monitorChatHook?.addAnalysisMessage) {
                monitorChatHook.addAnalysisMessage(result)
              }
            } catch (err) {
              console.error('Auto-analysis failed:', err)
            }
          }, 3000)
        } catch (err) {
          console.error('Failed to inject backend anomaly:', err)
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [sensorHook, monitorChatHook, setActivePanel])

  return (
    <Layout documents={documentsHook.documents}>
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', height: '100%' }}>

        {/* ── CHAT ASSISTANT — has its own history, PDF viewer, documents ── */}
        {activePanel === 'chat' && (
          <ChatPanel chatHook={chatHook} documentsHook={documentsHook} />
        )}

        {/* ── LIVE MONITOR INTELLIGENCE — separate monitorChatHook, no PDF viewer ── */}
        {activePanel === 'monitor' && (
          <MonitoringPanel
            sensorHook={sensorHook}
            chatHook={monitorChatHook}
            documentsHook={documentsHook}
          />
        )}

        {/* ── DOCUMENTS ── */}
        {activePanel === 'documents' && (
          <DocumentsView documentsHook={documentsHook} />
        )}

        {/* ── AI REPORTS ── */}
        {activePanel === 'reports' && <ReportsPanel />}

        {/* ── OPERATIONS LOGBOOK ── */}
        {activePanel === 'logbook' && <LogbookPanel />}
      </div>
    </Layout>
  )
}

// ── Documents section ─────────────────────────────────────────────────────────

function DocumentsView({ documentsHook }) {
  const { documents, isLoading, deleteDocument } = documentsHook
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [numPages, setNumPages] = useState(null)

  const TAG_COLORS = {
    'rolling-mill-main-drive-motor':        { bg: 'rgba(79,195,247,0.10)', border: 'var(--accent-blue-dim)', text: 'var(--accent-blue)' },
    'general-plant-motor':                  { bg: 'rgba(76,175,130,0.10)', border: '#2e7d5a',               text: '#4CAF82' },
    'industrial-induction-compressor-motor':{ bg: 'rgba(245,166,35,0.10)', border: 'var(--accent-amber-dim)', text: 'var(--accent-amber)' },
    'blower-large-motor-reference':         { bg: 'rgba(179,136,255,0.10)', border: '#7c5fa0',              text: '#b388ff' },
  }

  const handleSelectDoc = (doc) => {
    setSelectedDoc(doc)
    setCurrentPage(1)
    setNumPages(null)
  }

  const handleDelete = async (e, docId) => {
    e.stopPropagation()
    await deleteDocument(docId)
    if (selectedDoc?.doc_id === docId) setSelectedDoc(null)
  }

  const pdfUrl = selectedDoc
    ? `http://localhost:8000/pdf/${selectedDoc.doc_id}`
    : null

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>

      {/* ── Left: document list ─────────────────────────────── */}
      <div style={{
        width: 320,
        flexShrink: 0,
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          height: 44,
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          flexShrink: 0,
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.10em' }}>
            KNOWLEDGE LIBRARY
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
            {documents.length} docs
          </span>
        </div>

        {/* List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          {isLoading && (
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)', padding: '12px' }}>Loading...</p>
          )}
          {documents.length === 0 && !isLoading && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 200, gap: 8 }}>
              <span style={{ fontSize: 32 }}>📁</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
                No documents yet. Upload PDFs via Chat Assistant.
              </span>
            </div>
          )}

          {documents.map((doc) => {
            const isSelected = selectedDoc?.doc_id === doc.doc_id
            const tagStyle = TAG_COLORS[doc.equipment_tag] || {
              bg: 'rgba(139,146,176,0.10)', border: 'var(--border)', text: 'var(--text-muted)',
            }
            const isIndexed = (doc.chunk_count || 0) > 0

            return (
              <div
                key={doc.doc_id}
                onClick={() => handleSelectDoc(doc)}
                style={{
                  background: isSelected ? 'var(--bg-surface-3)' : 'var(--bg-surface)',
                  border: `1px solid ${isSelected ? 'var(--accent-amber-dim)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 12px',
                  marginBottom: 6,
                  cursor: 'pointer',
                  transition: 'var(--transition)',
                  position: 'relative',
                }}
                onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.borderColor = 'var(--border-active)' }}
                onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.borderColor = 'var(--border)' }}
              >
                {/* Selected indicator */}
                {isSelected && (
                  <div style={{
                    position: 'absolute', left: 0, top: 6, bottom: 6,
                    width: 3, borderRadius: '0 2px 2px 0',
                    background: 'var(--accent-amber)',
                  }} />
                )}

                {/* Doc name */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <span style={{ fontSize: 13, flexShrink: 0 }}>📄</span>
                  <span style={{
                    fontFamily: 'var(--font-sans)', fontSize: 12,
                    color: isSelected ? 'var(--accent-amber)' : 'var(--text-primary)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    fontWeight: isSelected ? 600 : 400,
                  }}>
                    {doc.doc_name}
                  </span>
                </div>

                {/* Badges row */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    <span style={{
                      fontFamily: 'var(--font-mono)', fontSize: 9, padding: '1px 6px',
                      borderRadius: 'var(--radius-sm)', border: `1px solid ${tagStyle.border}`,
                      background: tagStyle.bg, color: tagStyle.text, letterSpacing: '0.04em',
                      textTransform: 'uppercase', maxWidth: 130, overflow: 'hidden',
                      textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {doc.equipment_tag || 'General'}
                    </span>
                    <span style={{
                      fontFamily: 'var(--font-mono)', fontSize: 9,
                      color: isIndexed ? 'var(--status-ok)' : 'var(--accent-amber)',
                    }}>
                      {isIndexed ? `● ${doc.chunk_count} chunks` : '● processing'}
                    </span>
                  </div>

                  <button
                    onClick={(e) => handleDelete(e, doc.doc_id)}
                    title="Remove document"
                    style={{
                      fontFamily: 'var(--font-mono)', fontSize: 10,
                      color: 'var(--status-critical)',
                      border: '1px solid rgba(232,93,93,0.3)',
                      background: 'rgba(232,93,93,0.08)',
                      padding: '2px 8px', borderRadius: 'var(--radius-sm)',
                      cursor: 'pointer', letterSpacing: '0.04em',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(232,93,93,0.18)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(232,93,93,0.08)')}
                  >
                    REMOVE
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Right: inline PDF viewer ────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-base)' }}>
        {!selectedDoc ? (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: 12,
          }}>
            <span style={{ fontSize: 48, opacity: 0.3 }}>📄</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
              SELECT A DOCUMENT TO VIEW
            </span>
          </div>
        ) : (
          <>
            {/* PDF viewer header */}
            <div style={{
              height: 44, borderBottom: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '0 16px', flexShrink: 0,
            }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.08em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '60%' }}>
                {selectedDoc.doc_name}
              </span>
              {/* Page navigation */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  style={{
                    fontFamily: 'var(--font-mono)', fontSize: 11, padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)',
                    background: 'var(--bg-surface-2)', color: 'var(--text-secondary)',
                    cursor: currentPage <= 1 ? 'not-allowed' : 'pointer', opacity: currentPage <= 1 ? 0.4 : 1,
                  }}
                >
                  ‹ PREV
                </button>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                  {currentPage} / {numPages || '?'}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(numPages || p, p + 1))}
                  disabled={currentPage >= (numPages || 1)}
                  style={{
                    fontFamily: 'var(--font-mono)', fontSize: 11, padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)',
                    background: 'var(--bg-surface-2)', color: 'var(--text-secondary)',
                    cursor: currentPage >= (numPages || 1) ? 'not-allowed' : 'pointer',
                    opacity: currentPage >= (numPages || 1) ? 0.4 : 1,
                  }}
                >
                  NEXT ›
                </button>
                <button
                  onClick={() => setSelectedDoc(null)}
                  style={{
                    fontFamily: 'var(--font-mono)', fontSize: 11, padding: '3px 10px',
                    borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)',
                    background: 'var(--bg-surface-2)', color: 'var(--text-secondary)', cursor: 'pointer',
                  }}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Inline PDF iframe — simplest, most reliable */}
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <iframe
                key={`${selectedDoc.doc_id}-${currentPage}`}
                src={`${pdfUrl}#page=${currentPage}`}
                style={{ width: '100%', height: '100%', border: 'none', background: 'var(--bg-base)' }}
                title={selectedDoc.doc_name}
              />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
