import React, { useEffect, useCallback } from 'react'
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

  const chatHook = useChat()
  const documentsHook = useDocuments()

  // When an alert fires, we may want to auto-send to chat
  const handleAlertDetected = useCallback(() => {
    // Just increment — user clicks VIEW ANALYSIS to send the message
  }, [])

  const sensorHook = useSensorStream(handleAlertDetected)

  // Handle Ctrl+Shift+D demo shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault()
        sensorHook.triggerAnomaly('rm3', 'vibration')
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [sensorHook])

  const handleSendAlertToChat = useCallback(
    (query) => {
      setActivePanel('chat')
      chatHook.sendMessage(query, null)
    },
    [chatHook, setActivePanel]
  )

  return (
    <Layout documents={documentsHook.documents}>
      {/* Always render both panels; use CSS visibility/flex to control */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
          height: '100%',
        }}
      >
        {/* Chat panel — visible in chat mode or always as left panel */}
        <div
          style={{
            flex: '0 0 55%',
            display: activePanel === 'documents' || activePanel === 'reports' || activePanel === 'logbook' ? 'none' : 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            minWidth: 0,
          }}
        >
          <ChatPanel chatHook={chatHook} documentsHook={documentsHook} />
        </div>

        {/* Monitor panel — visible in monitor mode or as right panel alongside chat */}
        {(activePanel === 'monitor' || activePanel === 'chat') && (
          <div
            style={{
              flex: activePanel === 'monitor' ? 1 : '0 0 45%',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              minWidth: 0,
            }}
          >
            <MonitoringPanel
              sensorHook={sensorHook}
              onSendAlertToChat={handleSendAlertToChat}
              chatHook={chatHook}
            />
          </div>
        )}

        {/* Documents panel */}
        {activePanel === 'documents' && (
          <DocumentsView documentsHook={documentsHook} />
        )}

        {/* Reports panel */}
        {activePanel === 'reports' && (
          <ReportsPanel />
        )}

        {/* Logbook panel */}
        {activePanel === 'logbook' && (
          <LogbookPanel />
        )}
      </div>
    </Layout>
  )
}

function DocumentsView({ documentsHook }) {
  const { documents, isLoading, deleteDocument } = documentsHook

  return (
    <div style={{ flex: 1, padding: 20, overflowY: 'auto' }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.10em', marginBottom: 16 }}>
        KNOWLEDGE BASE — DOCUMENTS
      </div>
      {isLoading && (
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)' }}>Loading...</p>
      )}
      {documents.length === 0 && !isLoading && (
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-muted)' }}>
          No documents ingested yet. Upload a PDF from the Chat panel.
        </p>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {documents.map((doc) => (
          <div
            key={doc.doc_id}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>
                {doc.doc_name}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', marginTop: 4 }}>
                {doc.equipment_tag} · {doc.chunk_count} chunks
              </div>
            </div>
            <button
              onClick={() => deleteDocument(doc.doc_id)}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--status-critical)',
                border: '1px solid var(--status-critical)',
                background: 'rgba(232,93,93,0.10)',
                padding: '3px 10px',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
              }}
            >
              DELETE
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function PlaceholderPanel({ title, message }) {
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
      }}
    >
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.10em' }}>
        {title}
      </span>
      <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)' }}>
        {message}
      </p>
    </div>
  )
}
