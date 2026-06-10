import React, { useState } from 'react'
import CitationTag from './CitationTag'
import FeedbackForm from './FeedbackForm'
import { formatTimestamp } from '../../utils/formatters'
import useAppStore from '../../store/appStore'

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
  const setActivePanel = useAppStore((s) => s.setActivePanel)

  const handleFeedbackSuccess = (verdict) => {
    setFeedbackSubmitted(true)
    setShowFeedbackForm(false)
    if (onFeedbackSubmit) onFeedbackSubmit(verdict)
  }

  const handleViewReport = () => {
    setActivePanel('reports')
  }

  const handleViewLogbook = () => {
    setActivePanel('logbook')
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

export default function MessageBubble({ message, isLoading = false }) {
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

  return (
    <div
      style={{
        borderLeft: `2px solid ${message.isError ? 'var(--status-critical)' : 'var(--accent-amber)'}`,
        paddingLeft: 14,
        animation: 'fadeIn 0.2s ease',
      }}
    >
      {isAgentAnalysis ? (
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
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 6,
                marginTop: 10,
              }}
            >
              {message.citations.map((cit) => (
                <CitationTag key={cit.ref} citation={cit} />
              ))}
            </div>
          )}
        </>
      )}

      <div style={{ marginTop: 6 }}>
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
  )
}
