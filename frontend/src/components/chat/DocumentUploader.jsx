import React, { useState, useRef } from 'react'
import Spinner from '../shared/Spinner'

export default function DocumentUploader({ onUpload, isExpanded, onToggle }) {
  const [equipmentTag, setEquipmentTag] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef()

  const handleFile = async (file) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.')
      return
    }
    if (!equipmentTag.trim()) {
      setError('Please enter an equipment tag.')
      return
    }
    setError(null)
    setResult(null)
    setIsUploading(true)
    setProgress(0)

    // Simulate progress since axios doesn't easily track on small files
    const progressInterval = setInterval(() => {
      setProgress((p) => Math.min(p + 10, 90))
    }, 150)

    try {
      const res = await onUpload(file, equipmentTag.trim())
      clearInterval(progressInterval)
      setProgress(100)
      setResult(res)
      setEquipmentTag('')
    } catch (err) {
      clearInterval(progressInterval)
      setError(err.message)
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  if (!isExpanded) {
    return (
      <div
        style={{
          padding: '8px 16px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <button
          onClick={onToggle}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            color: 'var(--text-secondary)',
            fontSize: 13,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontFamily: 'var(--font-sans)',
          }}
        >
          <span>📎</span>
          <span>Attach document</span>
        </button>
        <input
          placeholder="Equipment tag..."
          value={equipmentTag}
          onChange={(e) => setEquipmentTag(e.target.value)}
          style={{
            flex: 1,
            padding: '4px 8px',
            fontSize: 12,
            borderRadius: 'var(--radius-sm)',
            height: 28,
          }}
        />
      </div>
    )
  }

  return (
    <div
      style={{
        borderTop: '1px solid var(--border)',
        padding: 16,
        background: 'var(--bg-surface)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.08em' }}>
          ATTACH DOCUMENT
        </span>
        <button
          onClick={onToggle}
          style={{ color: 'var(--text-muted)', fontSize: 16, lineHeight: 1 }}
        >
          ×
        </button>
      </div>

      {/* Equipment tag input */}
      <input
        placeholder="Equipment tag (e.g. Rolling Mill #3)"
        value={equipmentTag}
        onChange={(e) => setEquipmentTag(e.target.value)}
        style={{
          width: '100%',
          padding: '6px 10px',
          fontSize: 13,
          borderRadius: 'var(--radius-sm)',
          marginBottom: 10,
          height: 34,
        }}
      />

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `1px dashed ${isDragging ? 'var(--accent-amber)' : 'var(--border-active)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '20px 16px',
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragging ? 'var(--accent-amber-glow)' : 'transparent',
          transition: 'var(--transition)',
        }}
      >
        <div style={{ fontSize: 24, marginBottom: 6 }}>📄</div>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-secondary)' }}>
          Drop PDF here or <span style={{ color: 'var(--accent-amber)' }}>click to browse</span>
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
        />
      </div>

      {/* Progress */}
      {isUploading && (
        <div style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <Spinner size={12} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
              UPLOADING... {progress}%
            </span>
          </div>
          <div
            style={{
              height: 2,
              background: 'var(--border)',
              borderRadius: 1,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${progress}%`,
                background: 'var(--accent-amber)',
                transition: 'width 0.15s ease',
              }}
            />
          </div>
        </div>
      )}

      {/* Success */}
      {result && (
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ color: 'var(--status-ok)' }}>✓</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--status-ok)' }}>
            {result.chunk_count} chunks indexed — {result.doc_name}
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <p style={{ marginTop: 10, fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--status-critical)' }}>
          {error}
        </p>
      )}
    </div>
  )
}
