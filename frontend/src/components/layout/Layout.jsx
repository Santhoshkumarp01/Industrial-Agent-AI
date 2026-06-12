import React from 'react'
import TopBar from './TopBar'
import Sidebar from './Sidebar'

export default function Layout({ children, documents = [] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <TopBar />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar documents={documents} />
        <main
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
            {children}
          </div>
          {/* Footer badge */}
          <div style={{
            height: 28,
            borderTop: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--bg-surface)',
            gap: 16,
            flexShrink: 0,
          }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              AI: Phi-3.5-mini Fine-tuned (2K+ scenarios)
            </span>
            <span style={{ color: 'var(--border)' }}>|</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              RAG: Hybrid Search + Reranking
            </span>
            <span style={{ color: 'var(--border)' }}>|</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Vector DB: Qdrant Cloud
            </span>
          </div>
        </main>
      </div>
    </div>
  )
}
