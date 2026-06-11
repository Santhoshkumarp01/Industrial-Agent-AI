import React, { useRef, useEffect, useState } from 'react'
import MessageBubble from './MessageBubble'
import DocumentUploader from './DocumentUploader'
import PDFViewer from './PDFViewer'
import useAppStore from '../../store/appStore'

const DOT_GRID_BG = {
  backgroundImage: 'radial-gradient(circle, #1A1F2E 1px, transparent 1px)',
  backgroundSize: '20px 20px',
}

// Quick action prompts — prefill input with a structured query
const QUICK_ACTIONS = [
  { label: 'Fault Diagnosis',      icon: '🔍', prompt: 'Perform a fault diagnosis based on the uploaded manual. Identify the most likely fault causes and recommended actions.' },
  { label: 'Summarize Document',   icon: '📝', prompt: 'Summarize the key sections, safety rules, and maintenance procedures from the uploaded document.' },
  { label: 'Extract SOP',          icon: '📋', prompt: 'Extract all standard operating procedures (SOPs) from the document as a numbered step-by-step list.' },
  { label: 'Generate Report',      icon: '📊', prompt: 'Generate a structured maintenance report based on the document content including specifications, procedures, and safety requirements.' },
  { label: 'Inspection Checklist', icon: '✅', prompt: 'Create an inspection checklist based on the maintenance procedures in the document.' },
]

export default function ChatPanel({ chatHook, documentsHook }) {
  const { messages, isLoading, sendMessage } = chatHook
  const { uploadDocument, fetchDocuments } = documentsHook

  const selectedTag = useAppStore((s) => s.selectedEquipmentTag)
  const isPDFViewerOpen = useAppStore((s) => s.isPDFViewerOpen)

  const [inputValue, setInputValue] = useState('')
  const [uploaderExpanded, setUploaderExpanded] = useState(false)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text || isLoading) return
    sendMessage(text, selectedTag)
    setInputValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e) => {
    setInputValue(e.target.value)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 72) + 'px'
  }

  const handleUpload = async (file, tag) => {
    const result = await uploadDocument(file, tag)
    await fetchDocuments()
    return result
  }

  const handleQuickAction = (prompt) => {
    setInputValue(prompt)
    textareaRef.current?.focus()
  }

  const hasMessages = messages.length > 0

  return (
    <div
      style={{
        flex: isPDFViewerOpen ? '0 0 55%' : 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative',
        transition: 'flex var(--transition)',
      }}
    >
      {/* Panel header */}
      <div
        style={{
          height: 44,
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 14 }}>💬</span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--accent-amber)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            Chat Assistant — Document Intelligence
          </span>
        </div>

        {/* Equipment filter dropdown */}
        <select
          value={selectedTag || ''}
          onChange={(e) => {
            const v = e.target.value
            useAppStore.getState().setSelectedTag(v || null)
          }}
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: 12,
            padding: '4px 8px',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-secondary)',
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--border)',
            cursor: 'pointer',
          }}
        >
          <option value="">All Equipment</option>
          {documentsHook.documents
            .map((d) => d.equipment_tag)
            .filter((v, i, a) => v && a.indexOf(v) === i)
            .map((tag) => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
        </select>
      </div>

      {/* Quick actions bar — shown only when no messages yet */}
      {!hasMessages && (
        <div
          style={{
            borderBottom: '1px solid var(--border-subtle)',
            padding: '8px 16px',
            display: 'flex',
            gap: 6,
            flexWrap: 'wrap',
            flexShrink: 0,
            background: 'var(--bg-surface)',
          }}
        >
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--text-muted)',
              letterSpacing: '0.08em',
              alignSelf: 'center',
              marginRight: 4,
            }}
          >
            QUICK ACTIONS:
          </span>
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              onClick={() => handleQuickAction(action.prompt)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-sans)',
                fontSize: 11,
                cursor: 'pointer',
                transition: 'var(--transition)',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-amber-dim)'
                e.currentTarget.style.color = 'var(--accent-amber)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.color = 'var(--text-secondary)'
              }}
            >
              <span>{action.icon}</span>
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* Message history */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          ...(messages.length === 0 ? DOT_GRID_BG : {}),
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-sans)',
              fontSize: 13,
              textAlign: 'center',
              paddingTop: 60,
            }}
          >
            <span style={{ fontSize: 32 }}>🤖</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent-amber)', letterSpacing: '0.08em' }}>
              INDUSTRIAL AGENT AI
            </span>
            <span style={{ color: 'var(--text-secondary)', maxWidth: 340 }}>
              Upload a manual, SOP, or maintenance document and ask questions about it.
              Use quick actions above to get started instantly.
            </span>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isLoading && <MessageBubble isLoading />}
        <div ref={messagesEndRef} />
      </div>

      {/* Document uploader */}
      <DocumentUploader
        onUpload={handleUpload}
        isExpanded={uploaderExpanded}
        onToggle={() => setUploaderExpanded((p) => !p)}
      />

      {/* Input bar */}
      <div
        style={{
          height: 'auto',
          minHeight: 64,
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-surface)',
          flexShrink: 0,
        }}
      >
        {/* Equipment tag row */}
        <div
          style={{
            padding: '6px 12px 4px',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <label
            style={{
              fontSize: 10,
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              whiteSpace: 'nowrap',
            }}
          >
            Scope:
          </label>
          <select
            value={selectedTag || ''}
            onChange={(e) => {
              const v = e.target.value
              useAppStore.getState().setSelectedTag(v || null)
            }}
            style={{
              flex: 1,
              fontFamily: 'var(--font-sans)',
              fontSize: 12,
              padding: '3px 8px',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-secondary)',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border)',
              cursor: 'pointer',
            }}
          >
            <option value="">All Documents</option>
            {documentsHook.documents
              .map((d) => d.equipment_tag)
              .filter((v, i, a) => v && a.indexOf(v) === i)
              .map((tag) => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
          </select>
        </div>

        {/* Message input row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            padding: '8px 12px',
            gap: 8,
          }}
        >
          <button
            onClick={() => setUploaderExpanded((p) => !p)}
            style={{
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: uploaderExpanded ? 'var(--accent-amber)' : 'var(--text-secondary)',
              fontSize: 15,
              flexShrink: 0,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border)',
              background: 'var(--bg-surface-2)',
              transition: 'var(--transition)',
            }}
            title="Upload document"
          >
            📎
          </button>

          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask about maintenance procedures, equipment specs, fault diagnosis..."
            rows={1}
            style={{
              flex: 1,
              resize: 'none',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              fontFamily: 'var(--font-sans)',
              fontSize: 14,
              color: 'var(--text-primary)',
              lineHeight: 1.5,
              padding: '4px 0',
              overflowY: 'hidden',
            }}
          />

          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            style={{
              width: 32,
              height: 32,
              background: inputValue.trim() && !isLoading ? 'var(--accent-amber)' : 'var(--bg-surface-3)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transition: 'var(--transition)',
              color: 'var(--bg-base)',
              fontSize: 14,
              cursor: inputValue.trim() && !isLoading ? 'pointer' : 'not-allowed',
            }}
            title="Send (Enter)"
          >
            ▶
          </button>
        </div>
      </div>

      {/* PDF Viewer overlay */}
      <PDFViewer />
    </div>
  )
}
