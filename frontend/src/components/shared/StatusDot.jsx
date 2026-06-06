import React from 'react'

const STATUS_COLORS = {
  ok:       'var(--status-ok)',
  warning:  'var(--status-warn)',
  critical: 'var(--status-critical)',
  offline:  'var(--status-offline)',
}

const STATUS_ANIMATIONS = {
  ok:       'pulse-ok 2.5s ease-in-out infinite',
  warning:  'pulse-warn 1.5s ease-in-out infinite',
  critical: 'pulse-critical 0.9s ease-in-out infinite',
  offline:  'none',
}

const SIZES = {
  small:  8,
  medium: 10,
  large:  12,
}

export default function StatusDot({ status = 'ok', size = 'small' }) {
  const px = SIZES[size] || SIZES.small
  const color = STATUS_COLORS[status] || STATUS_COLORS.offline
  const animation = STATUS_ANIMATIONS[status] || 'none'

  return (
    <span
      style={{
        display: 'inline-block',
        width: px,
        height: px,
        borderRadius: '50%',
        backgroundColor: color,
        animation,
        flexShrink: 0,
      }}
      aria-label={`Status: ${status}`}
    />
  )
}
