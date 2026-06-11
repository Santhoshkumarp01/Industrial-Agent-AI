/**
 * MonitorChatPanel — AI chat for Live Monitor Intelligence.
 *
 * - Separate message history from Chat Assistant
 * - No document uploader, no PDF viewer
 * - Shows equipment prompt card when a machine card is clicked
 * - Prompt has quick-action buttons: run analysis, ask about fault, ask about maintenance
 */
import React, { useRef, useEffect, useState } from 'react'
import MessageBubble from '../chat/MessageBubble'

function EquipmentPromptCard({ prompt, onRunAnalysis, onQuickQuestion, isAnalyzing }) {
  const { machineName, severity, statusLine, latestLog } = prompt

  const sevDot = severity === 'CRITICAL' ? '🔴' : severity === 'WARNING' ? '🟡' : '🟢'

  const readings = latestLog ? [
    latestLog.vibration_mm_s != null && `VIB ${latestLog.vibration_mm_s}`,
    latestLog.bearing_temp_c != null && `TEMP ${latestLog.bearing_temp_c}°C`,
    latestLog.motor_current_a != null && `CURR ${latestLog.motor_current_a}A`,
    latestLog.rpm != null && `RPM ${latestLog.rpm}`,
  ].filter(Boolean) : []

  const quickQuestions = [
    `What is the current status of the ${machineName}?`,
    `What could cause this fault on the ${machineName}?`,
    `What maintenance action is recommended for the ${machineName}?`,
  ]

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
    }}>
      {/* Header — clean, no background colour */}
      <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ fontSize: 12 }}>{sevDot}</span>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-primary)', fontWeight: 600 }}>
            {machineName}
          </span>
        </div>
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-secondary)', paddingLeft: 20 }}>
          {statusLine}
        </div>
      </div>

      {/* Live readings — minimal tags */}
      {readings.length > 0 && (
        <div style={{ padding: '7px 12px', display: 'flex', gap: 5, flexWrap: 'wrap', borderBottom: '1px solid var(--border-subtle)' }}>
          {readings.map((r, i) => (
            <span key={i} style={{
              fontFamily: 'var(--font-mono)', fontSize: 10,
              color: 'var(--text-muted)',
              padding: '1px 6px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border)',
            }}>
              {r}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div style={{ padding: '10px 12px' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: 8 }}>
          WHAT WOULD YOU LIKE TO KNOW?
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 8 }}>
          {quickQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => onQuickQuestion(q)}
              disabled={isAnalyzing}
              style={{
                textAlign: 'left',
                padding: '6px 10px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                background: 'transparent',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-sans)',
                fontSize: 12,
                cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                opacity: isAnalyzing ? 0.5 : 1,
              }}
              onMouseEnter={(e) => {
                if (!isAnalyzing) {
                  e.currentTarget.style.borderColor = 'var(--border-active)'
                  e.currentTarget.style.color = 'var(--text-primary)'
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.color = 'var(--text-secondary)'
              }}
            >
              {q}
            </button>
          ))}
        </div>

        <button
          onClick={onRunAnalysis}
          disabled={isAnalyzing}
          style={{
            width: '100%',
            padding: '7px 12px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-active)',
            background: 'var(--bg-surface-2)',
            color: 'var(--accent-amber)',
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            cursor: isAnalyzing ? 'not-allowed' : 'pointer',
            letterSpacing: '0.06em',
            opacity: isAnalyzing ? 0.5 : 1,
          }}
        >
          RUN FULL AI ANALYSIS →
        </button>
      </div>
    </div>
  )
}

export default function MonitorChatPanel({ chatHook, isAnalyzing, onRunAnalysis }) {
  const { messages, isLoading, sendMessage } = chatHook
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, isAnalyzing])

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text || isLoading || isAnalyzing) return
    sendMessage(text, null)
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

  const handleQuickQuestion = (question) => {
    sendMessage(question, null)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{
        height: 44,
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 14px',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13 }}>🤖</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.08em' }}>
            AI ASSISTANT
          </span>
        </div>
        {isAnalyzing && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)', letterSpacing: '0.06em' }}>
            ⏳ ANALYZING...
          </span>
        )}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        {messages.map((msg) => {
          if (msg.isEquipmentPrompt) {
            return (
              <EquipmentPromptCard
                key={msg.id}
                prompt={msg.equipmentPrompt}
                isAnalyzing={isAnalyzing}
                onRunAnalysis={() => onRunAnalysis(
                  msg.equipmentPrompt.machineTag,
                  msg.equipmentPrompt.machineName
                )}
                onQuickQuestion={handleQuickQuestion}
              />
            )
          }
          return <MessageBubble key={msg.id} message={msg} />
        })}
        {isLoading && <MessageBubble isLoading />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ borderTop: '1px solid var(--border)', background: 'var(--bg-surface)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', padding: '8px 12px', gap: 8 }}>
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask about machine faults, procedures..."
            rows={1}
            disabled={isAnalyzing}
            style={{
              flex: 1,
              resize: 'none',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              fontFamily: 'var(--font-sans)',
              fontSize: 13,
              color: isAnalyzing ? 'var(--text-muted)' : 'var(--text-primary)',
              lineHeight: 1.5,
              padding: '4px 0',
              overflowY: 'hidden',
            }}
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading || isAnalyzing}
            style={{
              width: 30,
              height: 30,
              background: (inputValue.trim() && !isLoading && !isAnalyzing) ? 'var(--accent-amber)' : 'var(--bg-surface-3)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              color: 'var(--bg-base)',
              fontSize: 13,
              cursor: (inputValue.trim() && !isLoading && !isAnalyzing) ? 'pointer' : 'not-allowed',
              border: 'none',
              transition: 'var(--transition)',
            }}
          >
            ▶
          </button>
        </div>
      </div>
    </div>
  )
}
