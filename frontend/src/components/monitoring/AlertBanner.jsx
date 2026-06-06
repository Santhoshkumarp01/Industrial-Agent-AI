import React from 'react'
import StatusDot from '../shared/StatusDot'

export default function AlertBanner({ alert, onDismiss, onViewAnalysis }) {
  if (!alert) return null

  return (
    <div
      style={{
        background: 'rgba(232, 93, 93, 0.12)',
        border: '1px solid var(--status-critical)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        animation: 'slideDown 0.2s ease',
        margin: '8px 12px 0',
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, overflow: 'hidden' }}>
        <StatusDot status="critical" size="medium" />
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--status-critical)',
            letterSpacing: '0.04em',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          CRITICAL ALERT — {alert.equipmentName} — {alert.sensorKey} anomaly detected
          {' '}({alert.value?.toFixed(1)} {alert.unit || ''})
        </span>
      </div>

      <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
        <button
          onClick={() => onViewAnalysis(alert)}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--status-critical)',
            border: '1px solid var(--status-critical)',
            background: 'rgba(232, 93, 93, 0.12)',
            padding: '3px 10px',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            letterSpacing: '0.06em',
            transition: 'var(--transition)',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(232,93,93,0.22)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(232,93,93,0.12)'}
        >
          VIEW ANALYSIS
        </button>
        <button
          onClick={() => onDismiss(alert.id)}
          style={{
            color: 'var(--text-muted)',
            fontSize: 16,
            lineHeight: 1,
            padding: '2px 4px',
          }}
        >
          ×
        </button>
      </div>
    </div>
  )
}
