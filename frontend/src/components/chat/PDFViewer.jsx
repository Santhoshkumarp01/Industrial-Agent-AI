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
  const canvasRef = useRef(null)
  const containerRef = useRef(null)

  if (!isPDFViewerOpen || !activeCitation) return null

  // citation shape:
  // { doc_id, page_number, bbox: [x0, y0, x1, y1], doc_name, ref }
  const pdfUrl = getPDFUrl(activeCitation.doc_id)

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages)
  }

  // Draw amber highlight rectangle over bbox after page renders
  function onPageRenderSuccess(page) {
    // PDF coordinate space: origin bottom-left
    // Canvas coordinate space: origin top-left
    // We need to convert

    const canvas = containerRef.current?.querySelector('canvas')
    if (!canvas || !activeCitation.bbox) return

    const [x0, y0, x1, y1] = activeCitation.bbox

    // Get rendered page dimensions
    const canvasHeight = canvas.height
    const canvasWidth = canvas.width

    // page.originalWidth/Height are in PDF points
    const scaleX = canvasWidth / page.originalWidth
    const scaleY = canvasHeight / page.originalHeight

    // Convert PDF coords (bottom-left origin) to canvas coords (top-left origin)
    const rectX = x0 * scaleX
    const rectY = (page.originalHeight - y1) * scaleY
    const rectW = (x1 - x0) * scaleX
    const rectH = (y1 - y0) * scaleY

    // Draw on canvas using 2D context overlay
    // Create an overlay canvas on top of the pdf canvas
    const existing = containerRef.current?.querySelector('.bbox-overlay')
    if (existing) existing.remove()

    const overlay = document.createElement('canvas')
    overlay.className = 'bbox-overlay'
    overlay.width = canvasWidth
    overlay.height = canvasHeight
    overlay.style.position = 'absolute'
    overlay.style.top = canvas.offsetTop + 'px'
    overlay.style.left = canvas.offsetLeft + 'px'
    overlay.style.pointerEvents = 'none'
    overlay.style.zIndex = '10'

    const ctx = overlay.getContext('2d')
    ctx.fillStyle = 'rgba(245, 166, 35, 0.25)'   // amber semi-transparent fill
    ctx.strokeStyle = 'rgba(245, 166, 35, 0.9)'  // amber border
    ctx.lineWidth = 2
    ctx.fillRect(rectX, rectY, rectW, rectH)
    ctx.strokeRect(rectX, rectY, rectW, rectH)

    canvas.parentElement.style.position = 'relative'
    canvas.parentElement.appendChild(overlay)
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
            onRenderSuccess={onPageRenderSuccess}
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
