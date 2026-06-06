import React, { useState, useRef, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import useAppStore from '../../store/appStore'
import { getPdfUrl } from '../../services/api'

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`

export default function PDFViewer() {
  const { isPDFViewerOpen, activeCitation, closePDFViewer } = useAppStore()
  const [numPages, setNumPages] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState({ width: 0, height: 0 })
  const canvasRef = useRef(null)

  useEffect(() => {
    if (activeCitation?.page) {
      setCurrentPage(activeCitation.page)
    }
  }, [activeCitation])

  // Draw bbox highlight overlay after page renders
  const handlePageRenderSuccess = (page) => {
    setPageSize({ width: page.width, height: page.height })
  }

  useEffect(() => {
    if (!activeCitation?.bbox || !pageSize.width) return
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    canvas.width = pageSize.width
    canvas.height = pageSize.height
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const [x0, y0, x1, y1] = activeCitation.bbox
    // PDF coordinates have origin at bottom-left; canvas origin is top-left
    const canvasY = pageSize.height - y1
    const rectW = x1 - x0
    const rectH = y1 - y0

    ctx.fillStyle = 'rgba(245, 166, 35, 0.25)'
    ctx.strokeStyle = 'rgba(245, 166, 35, 0.8)'
    ctx.lineWidth = 1.5
    ctx.fillRect(x0, canvasY, rectW, rectH)
    ctx.strokeRect(x0, canvasY, rectW, rectH)
  }, [activeCitation, pageSize, currentPage])

  if (!isPDFViewerOpen) return null

  const docUrl = activeCitation?.docId ? getPdfUrl(activeCitation.docId) : null

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '45%',
        height: '100%',
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border)',
        zIndex: 200,
        display: 'flex',
        flexDirection: 'column',
        animation: 'slideInRight 0.2s ease',
      }}
    >
      {/* Header */}
      <div
        style={{
          height: 44,
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 14px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.08em' }}>
            PDF VIEWER
          </span>
          {activeCitation?.docName && (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--text-secondary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              — {activeCitation.docName}
            </span>
          )}
        </div>
        <button
          onClick={closePDFViewer}
          style={{
            color: 'var(--text-secondary)',
            fontSize: 18,
            lineHeight: 1,
            padding: 4,
          }}
        >
          ×
        </button>
      </div>

      {/* Page navigation */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '6px 14px',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage <= 1}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: currentPage <= 1 ? 'var(--text-muted)' : 'var(--text-secondary)',
            padding: '2px 8px',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-surface-2)',
          }}
        >
          ◀ PREV
        </button>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
          {currentPage} / {numPages || '—'}
        </span>
        <button
          onClick={() => setCurrentPage((p) => Math.min(numPages || p, p + 1))}
          disabled={!numPages || currentPage >= numPages}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: (!numPages || currentPage >= numPages) ? 'var(--text-muted)' : 'var(--text-secondary)',
            padding: '2px 8px',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-surface-2)',
          }}
        >
          NEXT ▶
        </button>
        {activeCitation?.sectionHeading && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', marginLeft: 'auto' }}>
            §{activeCitation.sectionHeading.slice(0, 30)}
          </span>
        )}
      </div>

      {/* PDF content */}
      <div style={{ flex: 1, overflow: 'auto', position: 'relative', background: 'var(--bg-base)' }}>
        {docUrl ? (
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <Document
              file={docUrl}
              onLoadSuccess={({ numPages }) => setNumPages(numPages)}
              loading={
                <div style={{ padding: 20, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
                  LOADING PDF...
                </div>
              }
              error={
                <div style={{ padding: 20, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--status-critical)' }}>
                  Failed to load PDF.
                </div>
              }
            >
              <Page
                pageNumber={currentPage}
                onRenderSuccess={handlePageRenderSuccess}
                renderAnnotationLayer={false}
                renderTextLayer={true}
              />
            </Document>
            {/* Highlight overlay canvas */}
            <canvas
              ref={canvasRef}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                pointerEvents: 'none',
              }}
            />
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--text-muted)',
            }}
          >
            NO DOCUMENT SELECTED
          </div>
        )}
      </div>
    </div>
  )
}
