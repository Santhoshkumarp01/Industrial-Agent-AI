import React from 'react'
import useAppStore from '../../store/appStore'

export default function CitationTag({ citation }) {
  const setActiveCitation = useAppStore((s) => s.setActiveCitation)

  const handleClick = () => {
    setActiveCitation({
      ref: citation.ref,
      doc_id: citation.doc_id,
      doc_name: citation.doc_name,
      page_number: citation.page_number,
      bbox: citation.bbox,
      section_heading: citation.section_heading,
    })
  }

  // Truncate snippet to at least 60 characters
  const displaySnippet = citation.snippet 
    ? citation.snippet.length > 60 
      ? citation.snippet.slice(0, 60) + '...'
      : citation.snippet
    : ''

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
        maxWidth: 450,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
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
      {displaySnippet && (
        <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>
          · {displaySnippet}
        </span>
      )}
    </button>
  )
}
