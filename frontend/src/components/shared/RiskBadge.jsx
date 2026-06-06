import React from 'react'

const RISK_STYLES = {
  CRITICAL: {
    bg: 'rgba(232, 93, 93, 0.12)',
    color: 'var(--status-critical)',
    border: 'var(--status-critical)',
  },
  HIGH: {
    bg: 'rgba(245, 166, 35, 0.12)',
    color: 'var(--accent-amber)',
    border: 'var(--accent-amber-dim)',
  },
  MEDIUM: {
    bg: 'rgba(79, 195, 247, 0.10)',
    color: 'var(--accent-blue)',
    border: 'var(--accent-blue-dim)',
  },
  LOW: {
    bg: 'rgba(76, 175, 130, 0.12)',
    color: 'var(--status-ok)',
    border: 'var(--status-ok)',
  },
  NORMAL: {
    bg: 'rgba(76, 175, 130, 0.10)',
    color: 'var(--status-ok)',
    border: 'var(--status-ok)',
  },
}

export default function RiskBadge({ level = 'NORMAL' }) {
  const key = level?.toUpperCase()
  const style = RISK_STYLES[key] || RISK_STYLES.NORMAL

  return (
    <span
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        letterSpacing: '0.08em',
        padding: '2px 7px',
        borderRadius: 'var(--radius-sm)',
        background: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
      }}
    >
      {key}
    </span>
  )
}
