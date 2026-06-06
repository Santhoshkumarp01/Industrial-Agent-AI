import React from 'react'
import useAppStore from '../../store/appStore'

export default function CitationTag({ citation }) {
  const setActiveCitation = useAppStore((s) => s.setActiveCitation)

  const handleClick = () => {
    setActiveCitation({
      docName: citation.doc_name,
      page: citation.page_number,
      bbox: citation.bbox,
      sectionHeading: citation.section_heading,
    })
  }

  return (
    <button
      onClick={handleClick}
      title={`${citation.doc_name} — ${citation.snippet}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        background: 'var(--accent-amber-glow)',
        border: '1px solid var(--accent-amber-dim)',
        borderRadius: 3,
        padding: '2px 8px',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--accent-amber)',
        cursor: 'pointer',
        transition: 'var(--transition)',
        whiteSpace: 'nowrap',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(245,166,35,0.2)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'var(--accent-amber-glow)'
      }}
    >
      {citation.ref}
      <span style={{ color: 'var(--text-secondary)', fontSize: 10 }}>
        Pg {citation.page_number}
      </span>
      {citation.section_heading && (
        <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>
          · {citation.section_heading.slice(0, 20)}
        </span>
      )}
    </button>
  )
}
