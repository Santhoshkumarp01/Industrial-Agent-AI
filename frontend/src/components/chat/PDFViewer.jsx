import { useState, useRef, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { getPDFUrl } from '../../services/api'
import useAppStore from '../../store/appStore'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Set worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`

export default function PDFViewer() {
  const { isPDFViewerOpen, activeCitation, closePDFViewer } = useAppStore()
  
  const [numPages, setNumPages] = useState(null)
  const [pageWidth, setPageWidth] = useState(600)
  const containerRef = useRef(null)

  if (!isPDFViewerOpen || !activeCitation) return null

  const pdfUrl = getPDFUrl(activeCitation.doc_id)

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages)
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: '45%',
        height: '100vh',
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        transform: 'translateX(0)',
        animation: 'slideInRight 200ms ease',
      }}
    >
      {/* Header */}
      <div
        style={{
          height: '48px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--accent-amber)',
            letterSpacing: '0.1em',
          }}
        >
          {activeCitation.ref} · {activeCitation.doc_name} · PAGE{' '}
          {activeCitation.page_number}
        </span>
        <button
          onClick={closePDFViewer}
          style={{
            background: 'none',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            borderRadius: 'var(--radius-sm)',
            padding: '4px 10px',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
          }}
        >
          CLOSE
        </button>
      </div>

      {/* PDF render area */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div
              style={{
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                marginTop: '40px',
              }}
            >
              LOADING PDF...
            </div>
          }
          error={
            <div
              style={{
                color: 'var(--status-critical)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                marginTop: '40px',
              }}
            >
              FAILED TO LOAD PDF
            </div>
          }
        >
          <Page
            pageNumber={activeCitation.page_number}
            width={pageWidth}
            renderTextLayer={true}
            renderAnnotationLayer={false}
          />
        </Document>
      </div>

      {/* Page info footer */}
      <div
        style={{
          height: '36px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--text-muted)',
          }}
        >
          PAGE {activeCitation.page_number} OF {numPages || '?'}
        </span>
      </div>
    </div>
  )
}
