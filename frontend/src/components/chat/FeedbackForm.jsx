import React, { useState } from 'react'
import { submitFeedback } from '../../services/api'

export default function FeedbackForm({ logbookEntryId, onSuccess }) {
  const [verdict, setVerdict] = useState('') // 'confirmed' or 'incorrect'
  const [actualRootCause, setActualRootCause] = useState('')
  const [actualActionTaken, setActualActionTaken] = useState('')
  const [outcome, setOutcome] = useState('')
  const [downtimeHours, setDowntimeHours] = useState('')
  const [engineerName, setEngineerName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isSubmitting || submitted) return

    setIsSubmitting(true)
    setError(null)

    try {
      const feedbackData = {
        logbook_entry_id: logbookEntryId,
        verdict,
        engineer_name: engineerName || 'Anonymous',
      }

      // Add optional fields only if verdict is incorrect
      if (verdict === 'incorrect') {
        if (actualRootCause) feedbackData.actual_root_cause = actualRootCause
        if (actualActionTaken) feedbackData.actual_action_taken = actualActionTaken
      }

      if (outcome) feedbackData.outcome = outcome
      if (downtimeHours) feedbackData.downtime_hours = parseFloat(downtimeHours)

      await submitFeedback(feedbackData)
      setSubmitted(true)
      if (onSuccess) onSuccess(verdict)
    } catch (err) {
      setError(err.message || 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div style={{
        background: 'rgba(93, 232, 145, 0.1)',
        border: '1px solid var(--status-ok)',
        borderRadius: 'var(--radius-sm)',
        padding: '12px',
        marginTop: '12px'
      }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--status-ok)',
          letterSpacing: '0.08em'
        }}>
          ✓ FEEDBACK SUBMITTED - Thank you for improving the system!
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} style={{
      background: 'var(--bg-surface-2)',
      border: '1px solid var(--border-active)',
      borderRadius: 'var(--radius-sm)',
      padding: '16px',
      marginTop: '16px'
    }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--accent-amber)',
        letterSpacing: '0.08em',
        marginBottom: '12px'
      }}>
        ENGINEER FEEDBACK
      </div>

      {/* Verdict Selection */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{
          display: 'block',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-secondary)',
          marginBottom: '8px'
        }}>
          Analysis Verdict *
        </label>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            type="button"
            onClick={() => setVerdict('confirmed')}
            style={{
              flex: 1,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              padding: '8px 12px',
              borderRadius: 'var(--radius-sm)',
              border: verdict === 'confirmed' ? '2px solid var(--status-ok)' : '1px solid var(--border-active)',
              background: verdict === 'confirmed' ? 'rgba(93, 232, 145, 0.15)' : 'var(--bg-surface-3)',
              color: verdict === 'confirmed' ? 'var(--status-ok)' : 'var(--text-secondary)',
              cursor: 'pointer',
              letterSpacing: '0.06em'
            }}
          >
            ✓ CONFIRMED
          </button>
          <button
            type="button"
            onClick={() => setVerdict('incorrect')}
            style={{
              flex: 1,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              padding: '8px 12px',
              borderRadius: 'var(--radius-sm)',
              border: verdict === 'incorrect' ? '2px solid var(--status-critical)' : '1px solid var(--border-active)',
              background: verdict === 'incorrect' ? 'rgba(232, 93, 93, 0.15)' : 'var(--bg-surface-3)',
              color: verdict === 'incorrect' ? 'var(--status-critical)' : 'var(--text-secondary)',
              cursor: 'pointer',
              letterSpacing: '0.06em'
            }}
          >
            ✗ INCORRECT
          </button>
        </div>
      </div>

      {/* If Incorrect - Show Correction Fields */}
      {verdict === 'incorrect' && (
        <>
          <div style={{ marginBottom: '16px' }}>
            <label style={{
              display: 'block',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--text-secondary)',
              marginBottom: '6px'
            }}>
              Actual Root Cause
            </label>
            <textarea
              value={actualRootCause}
              onChange={(e) => setActualRootCause(e.target.value)}
              placeholder="What was the real root cause?"
              rows={2}
              style={{
                width: '100%',
                fontFamily: 'var(--font-sans)',
                fontSize: 13,
                padding: '8px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-active)',
                background: 'var(--bg-surface-3)',
                color: 'var(--text-primary)',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{
              display: 'block',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--text-secondary)',
              marginBottom: '6px'
            }}>
              Actual Action Taken
            </label>
            <textarea
              value={actualActionTaken}
              onChange={(e) => setActualActionTaken(e.target.value)}
              placeholder="What action did you actually take?"
              rows={2}
              style={{
                width: '100%',
                fontFamily: 'var(--font-sans)',
                fontSize: 13,
                padding: '8px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-active)',
                background: 'var(--bg-surface-3)',
                color: 'var(--text-primary)',
                resize: 'vertical'
              }}
            />
          </div>
        </>
      )}

      {/* Outcome */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{
          display: 'block',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-secondary)',
          marginBottom: '6px'
        }}>
          Outcome
        </label>
        <select
          value={outcome}
          onChange={(e) => setOutcome(e.target.value)}
          style={{
            width: '100%',
            fontFamily: 'var(--font-sans)',
            fontSize: 13,
            padding: '8px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-active)',
            background: 'var(--bg-surface-3)',
            color: 'var(--text-primary)'
          }}
        >
          <option value="">Select outcome...</option>
          <option value="resolved">Resolved</option>
          <option value="partial">Partially Resolved</option>
          <option value="ongoing">Ongoing</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>

      {/* Downtime Hours */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{
          display: 'block',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-secondary)',
          marginBottom: '6px'
        }}>
          Downtime (hours)
        </label>
        <input
          type="number"
          step="0.1"
          value={downtimeHours}
          onChange={(e) => setDowntimeHours(e.target.value)}
          placeholder="0.0"
          style={{
            width: '100%',
            fontFamily: 'var(--font-sans)',
            fontSize: 13,
            padding: '8px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-active)',
            background: 'var(--bg-surface-3)',
            color: 'var(--text-primary)'
          }}
        />
      </div>

      {/* Engineer Name */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{
          display: 'block',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-secondary)',
          marginBottom: '6px'
        }}>
          Your Name
        </label>
        <input
          type="text"
          value={engineerName}
          onChange={(e) => setEngineerName(e.target.value)}
          placeholder="Engineer name"
          style={{
            width: '100%',
            fontFamily: 'var(--font-sans)',
            fontSize: 13,
            padding: '8px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-active)',
            background: 'var(--bg-surface-3)',
            color: 'var(--text-primary)'
          }}
        />
      </div>

      {/* Error Message */}
      {error && (
        <div style={{
          background: 'rgba(232, 93, 93, 0.1)',
          border: '1px solid var(--status-critical)',
          borderRadius: 'var(--radius-sm)',
          padding: '8px 12px',
          marginBottom: '12px',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--status-critical)'
        }}>
          {error}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!verdict || isSubmitting}
        style={{
          width: '100%',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          padding: '10px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--accent-amber)',
          background: verdict && !isSubmitting ? 'var(--accent-amber-glow)' : 'var(--bg-surface-3)',
          color: verdict && !isSubmitting ? 'var(--accent-amber)' : 'var(--text-muted)',
          cursor: verdict && !isSubmitting ? 'pointer' : 'not-allowed',
          letterSpacing: '0.08em',
          opacity: verdict && !isSubmitting ? 1 : 0.5
        }}
      >
        {isSubmitting ? 'SUBMITTING...' : 'SUBMIT FEEDBACK'}
      </button>
    </form>
  )
}
