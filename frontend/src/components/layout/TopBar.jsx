import React, { useState, useEffect } from 'react'
import { formatTimestamp } from '../../utils/formatters'
import StatusDot from '../shared/StatusDot'
import useAppStore from '../../store/appStore'

export default function TopBar() {
  const [time, setTime] = useState(new Date())
  const alertCount = useAppStore((s) => s.alertCount)

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <header
      style={{
        height: 48,
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        flexShrink: 0,
        zIndex: 100,
      }}
    >
      {/* Left — branding */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Logo icon */}
        <div
          style={{
            width: 28,
            height: 28,
            background: 'var(--accent-amber)',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              fontWeight: 600,
              color: 'var(--bg-base)',
              letterSpacing: '-0.02em',
            }}
          >
            IA
          </span>
        </div>

        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: '0.15em',
            color: 'var(--accent-amber)',
            textTransform: 'uppercase',
          }}
        >
          Industrial Agent
        </span>

        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>|</span>

        <span
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: 13,
            color: 'var(--text-secondary)',
          }}
        >
          Industrial Agent AI
        </span>
      </div>

      {/* Right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        {/* System status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <StatusDot status="ok" size="small" />
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--status-ok)',
              letterSpacing: '0.06em',
            }}
          >
            SYSTEM ONLINE
          </span>
        </div>

        {/* Notification bell */}
        <div style={{ position: 'relative' }}>
          <button
            style={{
              background: 'none',
              border: 'none',
              padding: 4,
              color: alertCount > 0 ? 'var(--status-critical)' : 'var(--text-secondary)',
              fontSize: 16,
              lineHeight: 1,
            }}
            aria-label="Alerts"
          >
            🔔
          </button>
          {alertCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                background: 'var(--status-critical)',
                color: '#fff',
                borderRadius: '50%',
                width: 14,
                height: 14,
                fontSize: 9,
                fontFamily: 'var(--font-mono)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 600,
              }}
            >
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          )}
        </div>

        {/* Clock */}
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--text-secondary)',
            letterSpacing: '0.05em',
          }}
        >
          {formatTimestamp(time)}
        </span>
      </div>
    </header>
  )
}
