import React from 'react'
import useAppStore from '../../store/appStore'

const NAV_ITEMS = [
  { id: 'monitor',   icon: '📡', label: 'Live Monitor Intelligence' },
  { id: 'chat',      icon: '💬', label: 'Chat Assistant' },
  { id: 'documents', icon: '📁', label: 'Documents' },
  { id: 'reports',   icon: '🗂️',  label: 'Analysis Reports' },
  { id: 'logbook',   icon: '📋', label: 'Operations Logbook' },
]

const SECTION_LABEL_STYLE = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  color: 'var(--text-muted)',
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  padding: '0 12px',
  marginBottom: 4,
  marginTop: 16,
  display: 'block',
}

export default function Sidebar({ documents = [] }) {
  const activePanel    = useAppStore((s) => s.activePanel)
  const selectedTag    = useAppStore((s) => s.selectedEquipmentTag)
  const setActivePanel = useAppStore((s) => s.setActivePanel)
  const setSelectedTag = useAppStore((s) => s.setSelectedTag)
  const setUserRole    = useAppStore((s) => s.setUserRole)

  const equipmentTags = [...new Set(documents.map((d) => d.equipment_tag).filter(Boolean))]
  const totalChunks   = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)

  const handleBackToHome = () => {
    if (confirm('Return to role selection? This will reset your session.')) {
      setUserRole(null)
    }
  }

  return (
    <aside
      style={{
        width: 220,
        flexShrink: 0,
        background: 'linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-base) 100%)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Back to Home button */}
      <div style={{ padding: '12px 12px 0' }}>
        <button
          onClick={handleBackToHome}
          style={{
            width: '100%',
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)',
            background: 'var(--bg-surface-2)',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            letterSpacing: '0.05em',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            transition: 'var(--transition)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--bg-surface-3)'
            e.currentTarget.style.borderColor = 'var(--border-active)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--bg-surface-2)'
            e.currentTarget.style.borderColor = 'var(--border)'
          }}
        >
          <span>🏠</span>
          <span>BACK TO HOME</span>
        </button>
      </div>

      {/* Navigation */}
      <nav style={{ marginTop: 8 }}>
        <span style={SECTION_LABEL_STYLE}>Navigation</span>
        {NAV_ITEMS.map((item) => {
          const isActive = activePanel === item.id
          return (
            <button
              key={item.id}
              onClick={() => setActivePanel(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                width: '100%',
                height: 36,
                padding: '0 12px',
                background: isActive ? 'var(--bg-surface-2)' : 'transparent',
                borderLeft: `2px solid ${isActive ? 'var(--accent-amber)' : 'transparent'}`,
                cursor: 'pointer',
                transition: 'var(--transition)',
                textAlign: 'left',
              }}
            >
              <span style={{ fontSize: 14 }}>{item.icon}</span>
              <span
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: 12,
                  color: isActive ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  transition: 'var(--transition)',
                  lineHeight: 1.2,
                }}
              >
                {item.label}
              </span>
            </button>
          )
        })}
      </nav>

      {/* Equipment tag filter */}
      {equipmentTags.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <span style={SECTION_LABEL_STYLE}>Filter by Equipment</span>
          <div style={{ padding: '0 10px', display: 'flex', flexDirection: 'column', gap: 4 }}>
            <button
              onClick={() => setSelectedTag(null)}
              style={{
                padding: '3px 10px',
                borderRadius: 'var(--radius-sm)',
                border: `1px solid ${!selectedTag ? 'var(--accent-amber-dim)' : 'var(--border)'}`,
                background: !selectedTag ? 'var(--accent-amber-glow)' : 'var(--bg-surface-2)',
                color: !selectedTag ? 'var(--accent-amber)' : 'var(--text-secondary)',
                fontFamily: 'var(--font-sans)',
                fontSize: 11,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'var(--transition)',
              }}
            >
              All Equipment
            </button>
            {equipmentTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag === selectedTag ? null : tag)}
                style={{
                  padding: '3px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${selectedTag === tag ? 'var(--accent-amber-dim)' : 'var(--border)'}`,
                  background: selectedTag === tag ? 'var(--accent-amber-glow)' : 'var(--bg-surface-2)',
                  color: selectedTag === tag ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-sans)',
                  fontSize: 11,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'var(--transition)',
                }}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Knowledge base stats */}
      <div style={{ marginTop: 'auto', padding: '14px 12px', borderTop: '1px solid var(--border-subtle)' }}>
        <span style={{ ...SECTION_LABEL_STYLE, padding: 0, marginTop: 0, marginBottom: 8 }}>
          Knowledge Base
        </span>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--text-secondary)',
            lineHeight: 1.8,
          }}
        >
          <div>
            <span style={{ color: 'var(--accent-amber)' }}>{documents.length}</span>
            {' '}Documents indexed
          </div>
          <div>
            <span style={{ color: 'var(--accent-blue)' }}>{totalChunks.toLocaleString()}</span>
            {' '}Chunks stored
          </div>
        </div>
      </div>
    </aside>
  )
}
