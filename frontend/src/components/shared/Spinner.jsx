import React from 'react'

export default function Spinner({ size = 16 }) {
  return (
    <span
      style={{
        display: 'inline-block',
        width: size,
        height: size,
        border: `2px solid var(--border-active)`,
        borderTopColor: 'var(--accent-amber)',
        borderRadius: '50%',
        animation: 'spin 0.7s linear infinite',
      }}
    />
  )
}

// Inject spin keyframe once
const style = document.createElement('style')
style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`
document.head.appendChild(style)
