import React, { useState } from 'react'
import CitationTag from './CitationTag'
import FeedbackForm from './FeedbackForm'
import { formatTimestamp } from '../../utils/formatters'
import useAppStore from '../../store/appStore'
import { submitChatFeedback } from '../../services/api'

function ThinkingDots() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 0' }}>
      <div style={{ display: 'flex', gap: 4 }}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: 'var(--accent-amber)',
              display: 'inline-block',
              animation: `dotBlink 1.4s ease-in-out infinite`,
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--accent-amber)',
          letterSpacing: '0.08em',
        }}
      >
        ANALYZING...
      </span>
    </div>
  )
}

function AgentAnalysisContent({ analysis, logbookEntryId, onFeedbackSubmit }) {
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const openLogbookEntry = useAppStore((s) => s.openLogbookEntry)
  const openReport = useAppStore((s) => s.openReport)

  const handleFeedbackSuccess = (verdict) => {
    setFeedbackSubmitted(true)
    setShowFeedbackForm(false)
    if (onFeedbackSubmit) onFeedbackSubmit(verdict)
  }

  const handleViewReport = () => {
    if (analysis.incident_id) {
      openReport(analysis.incident_id)
    }
  }

  const handleViewLogbook = () => {
    if (logbookEntryId) {
      openLogbookEntry(logbookEntryId)
    }
  }

  return (
    <div style={{ fontFamily: 'var(--font-sans)', fontSize: 14, lineHeight: 1.7 }}>
      {/* Header */}
      <div style={{ 
        background: 'rgba(232, 188, 93, 0.08)', 
        padding: '8px 12px', 
        borderRadius: 'var(--radius-sm)',
        marginBottom: 12,
        border: '1px solid rgba(232, 188, 93, 0.2)'
      }}>
        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 11, 
          color: 'var(--accent-amber)',
          letterSpacing: '0.08em',
          marginBottom: 4
        }}>
          MAINTENANCE ANALYSIS REPORT
        </div>
        <div style={{ color: 'var(--text-primary)', fontSize: 13 }}>
          <strong>{analysis.equipment_name}</strong> • Incident #{analysis.incident_id.substring(0, 8)}
        </div>
      </div>

      {/* Root Cause */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 10, 
          color: 'var(--accent-amber)',
          letterSpacing: '0.08em',
          marginBottom: 6
        }}>
          ROOT CAUSE
        </div>
        <div style={{ color: 'var(--text-primary)', marginBottom: 6, fontSize: 14 }}>
          <strong>{analysis.root_cause}</strong>
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.6 }}>
          {analysis.fault_description}
        </div>
        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 11, 
          color: 'var(--text-secondary)',
          marginTop: 6
        }}>
          Confidence: {(analysis.confidence_score * 100).toFixed(0)}%
        </div>
      </div>

      {/* Risk Assessment */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 10, 
          color: 'var(--accent-amber)',
          letterSpacing: '0.08em',
          marginBottom: 6
        }}>
          RISK ASSESSMENT
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ 
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            background: analysis.risk_level === 'CRITICAL' ? 'rgba(232, 93, 93, 0.15)' : 
                       analysis.risk_level === 'HIGH' ? 'rgba(232, 145, 93, 0.15)' :
                       analysis.risk_level === 'MEDIUM' ? 'rgba(232, 188, 93, 0.15)' : 'rgba(93, 232, 145, 0.15)',
            color: analysis.risk_level === 'CRITICAL' ? 'var(--status-critical)' :
                   analysis.risk_level === 'HIGH' ? '#e89143' :
                   analysis.risk_level === 'MEDIUM' ? 'var(--accent-amber)' : 'var(--status-ok)',
            border: `1px solid ${analysis.risk_level === 'CRITICAL' ? 'var(--status-critical)' :
                                 analysis.risk_level === 'HIGH' ? '#e89143' :
                                 analysis.risk_level === 'MEDIUM' ? 'var(--accent-amber)' : 'var(--status-ok)'}`
          }}>
            {analysis.risk_level}
          </span>
          <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
            Action required within <strong>{analysis.urgency_hours.toFixed(1)}h</strong>
          </span>
          {analysis.rul_hours && (
            <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              RUL: <strong>{analysis.rul_hours.toFixed(1)}h</strong>
            </span>
          )}
        </div>
        {analysis.parts_required && analysis.parts_required.length > 0 && (
          <div style={{ marginTop: 6, color: 'var(--text-secondary)', fontSize: 13 }}>
            Parts: {analysis.parts_required.join(', ')} 
            <span style={{ 
              marginLeft: 8,
              color: analysis.parts_available ? 'var(--status-ok)' : 'var(--status-warning)'
            }}>
              ({analysis.parts_available ? '✓ Available' : '⚠ Not in stock'})
            </span>
          </div>
        )}
      </div>

      {/* Immediate Actions */}
      {analysis.immediate_actions && analysis.immediate_actions.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ 
            fontFamily: 'var(--font-mono)', 
            fontSize: 10, 
            color: 'var(--accent-amber)',
            letterSpacing: '0.08em',
            marginBottom: 8
          }}>
            IMMEDIATE ACTIONS
          </div>
          <ol style={{ margin: 0, paddingLeft: 20, color: 'var(--text-primary)', fontSize: 13, lineHeight: 1.7 }}>
            {analysis.immediate_actions.slice(0, 5).map((action, i) => (
              <li key={i} style={{ marginBottom: 6 }}>{action}</li>
            ))}
          </ol>
          {analysis.immediate_actions.length > 5 && (
            <div style={{ 
              fontFamily: 'var(--font-mono)', 
              fontSize: 11, 
              color: 'var(--text-secondary)',
              marginTop: 6
            }}>
              + {analysis.immediate_actions.length - 5} more actions
            </div>
          )}
        </div>
      )}

      {/* Repair Steps */}
      {analysis.repair_steps && analysis.repair_steps.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ 
            fontFamily: 'var(--font-mono)', 
            fontSize: 10, 
            color: 'var(--accent-amber)',
            letterSpacing: '0.08em',
            marginBottom: 8
          }}>
            REPAIR PROCEDURE
          </div>
          <ol style={{ margin: 0, paddingLeft: 20, color: 'var(--text-primary)', fontSize: 13, lineHeight: 1.7 }}>
            {analysis.repair_steps.slice(0, 5).map((step, i) => (
              <li key={i} style={{ marginBottom: 6 }}>{step}</li>
            ))}
          </ol>
          {analysis.repair_steps.length > 5 && (
            <div style={{ 
              fontFamily: 'var(--font-mono)', 
              fontSize: 11, 
              color: 'var(--text-secondary)',
              marginTop: 6
            }}>
              + {analysis.repair_steps.length - 5} more steps
            </div>
          )}
        </div>
      )}

      {/* Feedback Section */}
      <div style={{ 
        marginTop: 16, 
        paddingTop: 12, 
        borderTop: '1px solid var(--border-subtle)'
      }}>
        {!feedbackSubmitted && !showFeedbackForm && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <button
              onClick={() => setShowFeedbackForm(true)}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--accent-amber)',
                background: 'var(--accent-amber-glow)',
                color: 'var(--accent-amber)',
                cursor: 'pointer',
                letterSpacing: '0.06em'
              }}
            >
              📝 PROVIDE FEEDBACK
            </button>
            <button
              onClick={handleViewLogbook}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-active)',
                background: 'transparent',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                letterSpacing: '0.06em'
              }}
            >
              📋 VIEW IN LOGBOOK
            </button>
            <button
              onClick={handleViewReport}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-active)',
                background: 'transparent',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                letterSpacing: '0.06em',
                marginLeft: 'auto'
              }}
            >
              📊 VIEW REPORT →
            </button>
          </div>
        )}

        {showFeedbackForm && !feedbackSubmitted && (
          <FeedbackForm 
            logbookEntryId={logbookEntryId}
            onSuccess={handleFeedbackSuccess}
          />
        )}

        {feedbackSubmitted && (
          <div style={{
            background: 'rgba(93, 232, 145, 0.1)',
            border: '1px solid var(--status-ok)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--status-ok)',
              letterSpacing: '0.08em'
            }}>
              ✓ FEEDBACK RECORDED - Thank you!
            </span>
            <button
              onClick={handleViewLogbook}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--status-ok)',
                background: 'transparent',
                color: 'var(--status-ok)',
                cursor: 'pointer',
                letterSpacing: '0.06em',
                marginLeft: 'auto'
              }}
            >
              VIEW IN LOGBOOK
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Machine Analysis Content (With Feedback Form) ────────────────────────────
function MachineAnalysisContent({ data, logbookEntryId, onFeedbackSubmit }) {
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const setActivePanel = useAppStore((s) => s.setActivePanel)
  const setActiveCitation = useAppStore((s) => s.setActiveCitation)
  const openLogbookEntry = useAppStore((s) => s.openLogbookEntry)
  const openReport = useAppStore((s) => s.openReport)

  const handleFeedbackSuccess = (verdict) => {
    setFeedbackSubmitted(true)
    setShowFeedbackForm(false)
    if (onFeedbackSubmit) onFeedbackSubmit(verdict)
  }

  const handleViewReport = () => {
    if (data.incident_id) {
      openReport(data.incident_id)
    }
  }

  const handleViewLogbook = () => {
    if (logbookEntryId) {
      openLogbookEntry(logbookEntryId)
    }
  }

  if (!data) return null

  const analysis       = data.analysis || {}
  const readings       = data.latest_readings || {}
  const severity       = data.current_severity || 'UNKNOWN'
  const faultCode      = data.fault_code || '—'
  const eventSummary   = data.event_summary || ''
  const mappedDoc      = data.mapped_document || ''
  const answerText     = analysis.answer || ''
  const rawCitations   = analysis.citations || []
  const isGrounded     = analysis.grounded_in_doc

  // Map citations to CitationTag format
  const citations = rawCitations.map((cit) => ({
    ref: cit.ref || `[C${cit.chunk_id || '?'}]`,
    doc_id: cit.doc_id || data.doc_id,
    doc_name: cit.doc_name || mappedDoc,
    page_number: cit.page || cit.page_number || 1,
    section_heading: cit.section || cit.section_heading || '',
    snippet: cit.snippet || cit.text?.substring(0, 100) || '',
    bbox: null  // Remove bbox - not working correctly
  }))

  const SEV_COLOR = {
    CRITICAL: 'var(--status-critical)',
    WARNING:  'var(--accent-amber)',
    NORMAL:   'var(--status-ok)',
    UNKNOWN:  'var(--text-muted)',
  }

  return (
    <div style={{ fontFamily: 'var(--font-sans)', fontSize: 14, lineHeight: 1.7 }}>

      {/* Header */}
      <div style={{
        background: 'rgba(232,188,93,0.08)',
        padding: '8px 12px',
        borderRadius: 'var(--radius-sm)',
        marginBottom: 12,
        border: '1px solid rgba(232,188,93,0.2)',
      }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.08em', marginBottom: 4 }}>
          MACHINE ANALYSIS REPORT
        </div>
        <div style={{ color: 'var(--text-primary)', fontSize: 13 }}>
          <strong>{data.display_name}</strong>
          {' · '}
          <span style={{ color: SEV_COLOR[severity] || 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            {severity}
          </span>
          {faultCode !== '—' && (
            <span style={{ marginLeft: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
              {faultCode}
            </span>
          )}
        </div>
        {eventSummary && (
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 4 }}>{eventSummary}</div>
        )}
      </div>

      {/* Latest sensor readings */}
      {Object.keys(readings).length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)', letterSpacing: '0.08em', marginBottom: 6 }}>
            CURRENT SENSOR READINGS
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {readings.vibration_mm_s != null && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-surface-2)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                VIB {readings.vibration_mm_s} mm/s
              </span>
            )}
            {readings.bearing_temp_c != null && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-surface-2)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                TEMP {readings.bearing_temp_c}°C
              </span>
            )}
            {readings.motor_current_a != null && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-surface-2)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                CURR {readings.motor_current_a} A
              </span>
            )}
            {readings.lube_pressure_bar != null && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-surface-2)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                PRES {readings.lube_pressure_bar} bar
              </span>
            )}
            {readings.rpm != null && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-surface-2)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                RPM {readings.rpm}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Document-grounded LLM answer */}
      {answerText && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)', letterSpacing: '0.08em', marginBottom: 8 }}>
            AI DIAGNOSIS & RECOMMENDATION
            {isGrounded && (
              <span style={{ marginLeft: 8, color: 'var(--status-ok)', fontSize: 10 }}>● GROUNDED IN MANUAL</span>
            )}
          </div>
          
          {/* Parse and format the structured response */}
          {(() => {
            const sections = []
            let currentText = answerText
            
            // Extract sections with bold headers and lists
            const sectionRegex = /\*\*([^*]+)\*\*\s*([^*]*?)(?=\*\*|$)/g
            let match
            
            while ((match = sectionRegex.exec(answerText)) !== null) {
              const [, header, content] = match
              sections.push({ header: header.trim(), content: content.trim() })
            }
            
            if (sections.length === 0) {
              // No structured format, display as-is
              return (
                <p style={{ color: 'var(--text-primary)', fontSize: 13, lineHeight: 1.75, whiteSpace: 'pre-wrap', margin: 0 }}>
                  {answerText}
                </p>
              )
            }
            
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {sections.map((section, idx) => {
                  const { header, content } = section
                  
                  // Parse array lists like ['item1', 'item2']
                  const listMatch = content.match(/\[(.*?)\]/)
                  
                  if (listMatch && content.includes("'")) {
                    try {
                      const items = listMatch[1]
                        .split(/,\s*/)
                        .map(item => item.replace(/^['"]|['"]$/g, '').trim())
                        .filter(item => item.length > 0)
                      
                      return (
                        <div key={idx}>
                          <div style={{ 
                            fontWeight: 600, 
                            color: 'var(--accent-amber)', 
                            marginBottom: 6,
                            fontSize: 13
                          }}>
                            {header}:
                          </div>
                          <ol style={{ 
                            margin: 0, 
                            paddingLeft: 24, 
                            color: 'var(--text-primary)',
                            fontSize: 13,
                            lineHeight: 1.7
                          }}>
                            {items.slice(0, 6).map((item, i) => (
                              <li key={i} style={{ marginBottom: 4 }}>{item}</li>
                            ))}
                          </ol>
                          {items.length > 6 && (
                            <div style={{ 
                              fontFamily: 'var(--font-mono)', 
                              fontSize: 11, 
                              color: 'var(--text-muted)',
                              marginTop: 4,
                              paddingLeft: 24
                            }}>
                              + {items.length - 6} more items
                            </div>
                          )}
                        </div>
                      )
                    } catch (e) {
                      // Parsing failed, show as text
                      return (
                        <div key={idx}>
                          <strong style={{ color: 'var(--accent-amber)' }}>{header}:</strong>{' '}
                          <span style={{ color: 'var(--text-primary)' }}>{content}</span>
                        </div>
                      )
                    }
                  }
                  
                  // Regular text section
                  return (
                    <div key={idx} style={{ color: 'var(--text-primary)', fontSize: 13, lineHeight: 1.7 }}>
                      <strong style={{ color: 'var(--accent-amber)' }}>{header}:</strong>{' '}
                      {content}
                    </div>
                  )
                })}
              </div>
            )
          })()}
        </div>
      )}

      {/* Citations */}
      {citations.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)', letterSpacing: '0.08em', marginBottom: 6 }}>
            MANUAL REFERENCES
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {citations.map((cit, i) => (
              <CitationTag key={i} citation={cit} />
            ))}
          </div>
        </div>
      )}

      {/* Source document */}
      {mappedDoc && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
            📄 Source: {mappedDoc}
          </div>
        </div>
      )}

      {/* Footer actions - With feedback form for continuous learning */}
      <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--border-subtle)' }}>
        {!feedbackSubmitted && !showFeedbackForm && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button
              onClick={() => setShowFeedbackForm(true)}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--accent-amber)',
                background: 'var(--accent-amber-glow)',
                color: 'var(--accent-amber)',
                cursor: 'pointer',
                letterSpacing: '0.06em'
              }}
            >
              📝 PROVIDE FEEDBACK
            </button>
            <button
              onClick={handleViewLogbook}
              style={{ fontFamily: 'var(--font-mono)', fontSize: 11, padding: '5px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-active)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', letterSpacing: '0.05em' }}
            >
              📋 VIEW IN LOGBOOK
            </button>
            <button
              onClick={handleViewReport}
              style={{ fontFamily: 'var(--font-mono)', fontSize: 11, padding: '5px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-active)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', letterSpacing: '0.05em', marginLeft: 'auto' }}
            >
              📊 VIEW REPORTS →
            </button>
          </div>
        )}

        {showFeedbackForm && !feedbackSubmitted && (
          <FeedbackForm 
            logbookEntryId={logbookEntryId}
            onSuccess={handleFeedbackSuccess}
          />
        )}

        {feedbackSubmitted && (
          <div style={{
            background: 'rgba(93, 232, 145, 0.1)',
            border: '1px solid var(--status-ok)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--status-ok)',
              letterSpacing: '0.08em'
            }}>
              ✓ FEEDBACK RECORDED - Thank you!
            </span>
            <button
              onClick={handleViewLogbook}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--status-ok)',
                background: 'transparent',
                color: 'var(--status-ok)',
                cursor: 'pointer',
                letterSpacing: '0.06em',
                marginLeft: 'auto'
              }}
            >
              VIEW IN LOGBOOK
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function MessageBubble({ message, isLoading = false }) {
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackGiven, setFeedbackGiven] = useState(false)
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false)
  
  const handleChatFeedback = async (verdict) => {
    setFeedbackSubmitting(true)
    try {
      // Generate a message ID from timestamp
      const messageId = message.timestamp ? new Date(message.timestamp).getTime().toString() : Date.now().toString()
      
      // Get session ID from message or use a default
      const sessionId = message.sessionId || 'default-session'
      
      await submitChatFeedback(
        sessionId,
        messageId,
        message.originalQuery || message.content || '',
        message.content,
        verdict
      )
      
      setFeedbackGiven(true)
      console.log(`✓ Chat feedback submitted: ${verdict}`)
    } catch (err) {
      console.error('Failed to submit chat feedback:', err)
      // Still mark as given to prevent re-submission
      setFeedbackGiven(true)
    } finally {
      setFeedbackSubmitting(false)
    }
  }
  
  if (isLoading) {
    return (
      <div style={{ padding: '4px 0 4px 16px', borderLeft: '2px solid var(--accent-amber)' }}>
        <ThinkingDots />
      </div>
    )
  }

  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          animation: 'fadeIn 0.2s ease',
        }}
      >
        <div
          style={{
            maxWidth: '80%',
            background: 'var(--bg-surface-3)',
            border: '1px solid var(--border-active)',
            borderRadius: '6px 6px 2px 6px',
            padding: '10px 14px',
          }}
        >
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 14, color: 'var(--text-primary)' }}>
            {message.content}
          </p>
          <div style={{ textAlign: 'right', marginTop: 4 }}>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--text-muted)',
              }}
            >
              {formatTimestamp(message.timestamp)}
            </span>
          </div>
        </div>
      </div>
    )
  }

  // Assistant message - check if it's an agent analysis
  const isAgentAnalysis = message.analysisData && message.logbookEntryId
  const isMachineAnalysis = message.isMachineAnalysis && message.analysisData

  return (
    <div
      style={{
        borderLeft: `2px solid ${message.isError ? 'var(--status-critical)' : 'var(--accent-amber)'}`,
        paddingLeft: 14,
        animation: 'fadeIn 0.2s ease',
      }}
    >
      {isMachineAnalysis ? (
        <MachineAnalysisContent 
          data={message.analysisData} 
          logbookEntryId={message.logbookEntryId}
          onFeedbackSubmit={message.onFeedbackSubmit}
        />
      ) : isAgentAnalysis ? (
        <AgentAnalysisContent
          analysis={message.analysisData}
          logbookEntryId={message.logbookEntryId}
          onFeedbackSubmit={message.onFeedbackSubmit}
        />
      ) : (
        <>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 14,
              color: message.isError ? 'var(--status-critical)' : 'var(--text-primary)',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.7,
            }}
          >
            {message.content}
          </p>

          {message.citations && message.citations.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
              {message.citations.map((cit) => (
                <CitationTag key={cit.ref} citation={cit} />
              ))}
            </div>
          )}
          
          {/* Engineer Feedback for Chat Answers */}
          {!message.isError && message.citations && message.citations.length > 0 && (
            <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--border-subtle)' }}>
              {!feedbackGiven ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
                    Was this answer helpful?
                  </span>
                  <button
                    onClick={() => handleChatFeedback('positive')}
                    disabled={feedbackSubmitting}
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--status-ok)',
                      background: 'rgba(93, 232, 145, 0.1)',
                      color: 'var(--status-ok)',
                      cursor: feedbackSubmitting ? 'wait' : 'pointer',
                      letterSpacing: '0.06em',
                      opacity: feedbackSubmitting ? 0.6 : 1
                    }}
                  >
                    ✓ YES
                  </button>
                  <button
                    onClick={() => handleChatFeedback('negative')}
                    disabled={feedbackSubmitting}
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--status-warning)',
                      background: 'rgba(232, 188, 93, 0.1)',
                      color: 'var(--status-warning)',
                      cursor: feedbackSubmitting ? 'wait' : 'pointer',
                      letterSpacing: '0.06em',
                      opacity: feedbackSubmitting ? 0.6 : 1
                    }}
                  >
                    ✗ NO
                  </button>
                </div>
              ) : (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
                  ✓ Thank you for your feedback!
                </div>
              )}
            </div>
          )}
        </>
      )}

      <div style={{ marginTop: 6 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </div>
  )
}
