import React, { useRef, useEffect, useState } from 'react'
import MessageBubble from './MessageBubble'
import DocumentUploader from './DocumentUploader'
import PDFViewer from './PDFViewer'
import useAppStore from '../../store/appStore'

const DOT_GRID_BG = {
  backgroundImage: 'radial-gradient(circle, #1A1F2E 1px, transparent 1px)',
  backgroundSize: '20px 20px',
}

export default function ChatPanel({ chatHook, documentsHook }) {
  const { messages, isLoading, sendMessage } = chatHook
  const { uploadDocument, fetchDocuments } = documentsHook

  const selectedTag = useAppStore((s) => s.selectedEquipmentTag)
  const isPDFViewerOpen = useAppStore((s) => s.isPDFViewerOpen)

  const [inputValue, setInputValue] = useState('')
  const [uploaderExpanded, setUploaderExpanded] = useState(false)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text || isLoading) return
    sendMessage(text, selectedTag)
    setInputValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e) => {
    setInputValue(e.target.value)
    // Auto-grow textarea (max 3 lines)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 72) + 'px'
  }

  const handleUpload = async (file, tag) => {
    const result = await uploadDocument(file, tag)
    await fetchDocuments()
    return result
  }

  return (
    <div
      style={{
        flex: isPDFViewerOpen ? '0 0 55%' : 1,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid var(--border)',
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
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--accent-amber)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          Chat Assistant
        </span>
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

      {/* Message history */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          ...(messages.length <= 1 ? DOT_GRID_BG : {}),
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-sans)',
              fontSize: 13,
              textAlign: 'center',
            }}
          >
            Upload a document and ask your first question.
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
          display: 'flex',
          alignItems: 'flex-end',
          padding: '10px 12px',
          gap: 8,
          flexShrink: 0,
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
            fontSize: 16,
            flexShrink: 0,
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)',
            background: 'var(--bg-surface-2)',
            transition: 'var(--transition)',
          }}
          title="Attach document"
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

      {/* PDF Viewer overlay */}
      <PDFViewer />
    </div>
  )
}
