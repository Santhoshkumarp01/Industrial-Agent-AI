import React, { useState, useEffect } from 'react'

export default function QuickStartGuide() {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Show only on first visit
    const hasSeenGuide = localStorage.getItem('hasSeenQuickStart')
    if (!hasSeenGuide) {
      setIsVisible(true)
    }
  }, [])

  const handleDismiss = () => {
    localStorage.setItem('hasSeenQuickStart', 'true')
    setIsVisible(false)
  }

  if (!isVisible) return null

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
    }}>
      <div style={{
        background: 'var(--bg-surface-2)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
        maxWidth: 520,
        width: '90%',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 20,
        }}>
          <h2 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--accent-amber)',
            letterSpacing: '0.08em',
            margin: 0,
          }}>
            QUICK START GUIDE
          </h2>
          <button
            onClick={handleDismiss}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--text-muted)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          
          <Step
            number="1"
            title="Test with Demo Anomaly"
            description="Go to Live Monitor Intelligence → Click DEMO ANOMALY button → Watch AI analysis with PDF citations"
          />

          <Step
            number="2"
            title="Chat with AI Assistant"
            description="Navigate to Chat Assistant → Ask questions like 'What causes bearing failure?' → Get cited answers from manuals"
          />

          <Step
            number="3"
            title="Upload Equipment Manuals"
            description="In Chat Assistant → Upload PDF manual → Select equipment tag → Wait for indexing (30-60s)"
          />

          <Step
            number="4"
            title="View Analysis Reports"
            description="Check Analysis Reports panel → Review Operations Logbook → Monitor equipment health status"
          />
        </div>

        {/* Tip */}
        <div style={{
          marginTop: 20,
          padding: 12,
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
        }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
          }}>
            NOTE: All AI answers include PDF page citations with highlighting. Click any citation to view the source document.
          </span>
        </div>

        {/* Dismiss button */}
        <button
          onClick={handleDismiss}
          style={{
            marginTop: 20,
            width: '100%',
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            padding: '10px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)',
            background: 'var(--bg-surface-3)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            letterSpacing: '0.04em',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--bg-surface-3)')}
        >
          GOT IT
        </button>
      </div>
    </div>
  )
}

function Step({ number, title, description }) {
  return (
    <div style={{ display: 'flex', gap: 12 }}>
      <div style={{
        width: 24,
        height: 24,
        borderRadius: '50%',
        background: 'var(--accent-amber)',
        color: 'var(--bg-base)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        fontWeight: 600,
        flexShrink: 0,
      }}>
        {number}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{
          fontFamily: 'var(--font-sans)',
          fontSize: 12,
          color: 'var(--text-primary)',
          fontWeight: 500,
          marginBottom: 4,
        }}>
          {title}
        </div>
        <div style={{
          fontFamily: 'var(--font-sans)',
          fontSize: 11,
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
        }}>
          {description}
        </div>
      </div>
    </div>
  )
}
