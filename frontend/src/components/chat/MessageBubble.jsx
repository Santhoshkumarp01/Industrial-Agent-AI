import React from 'react'
import CitationTag from './CitationTag'
import { formatTimestamp } from '../../utils/formatters'

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

  // Assistant message
  return (
    <div
      style={{
        borderLeft: `2px solid ${message.isError ? 'var(--status-critical)' : 'var(--accent-amber)'}`,
        paddingLeft: 14,
        animation: 'fadeIn 0.2s ease',
      }}
    >
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
