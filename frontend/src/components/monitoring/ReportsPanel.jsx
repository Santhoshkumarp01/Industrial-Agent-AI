import React, { useEffect, useState } from 'react'
import { getReports, getReport } from '../../services/api'
import Spinner from '../shared/Spinner'
import useAppStore from '../../store/appStore'
import CitationTag from '../chat/CitationTag'

export default function ReportsPanel() {
  const [reports, setReports] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterEquipment, setFilterEquipment] = useState('')
  
  // Get selected report from store
  const selectedReportId = useAppStore((s) => s.selectedReportId)
  const clearReportSelection = useAppStore((s) => s.clearReportSelection)

  useEffect(() => {
    loadReports()
    // Removed auto-refresh - reports only load on mount or manual refresh
  }, [])
  
  // Auto-open selected report from store
  useEffect(() => {
    if (selectedReportId && reports.length > 0) {
      handleReportClick(selectedReportId)
      // Scroll to the report
      setTimeout(() => {
        const element = document.getElementById(`report-${selectedReportId}`)
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }, 100)
      // Clear selection after 5 seconds
      setTimeout(() => clearReportSelection(), 5000)
    }
  }, [selectedReportId, reports])

  const loadReports = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getReports(null, 100)
      setReports(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReportClick = async (reportId) => {
    try {
      const data = await getReport(reportId)
      setSelectedReport(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleExportReport = (report) => {
    const dataStr = JSON.stringify(report, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${report.report_id || 'export'}_${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleExportAll = () => {
    const dataStr = JSON.stringify(filteredReports, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `all_reports_${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const filteredReports = filterEquipment
    ? reports.filter((r) => 
        r.incident_summary?.equipment_id?.toLowerCase().includes(filterEquipment.toLowerCase())
      )
    : reports

  if (isLoading) {
    return (
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <Spinner />
      </div>
    )
  }

  return (
    <div style={{ 
      flex: 1, 
      display: 'flex', 
      overflow: 'hidden',
      background: 'var(--bg-base)'
    }}>
      {/* Reports List */}
      <div style={{ 
        flex: '0 0 40%', 
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{ 
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
        }}>
          <div style={{ 
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 12
          }}>
            <div style={{ 
              fontFamily: 'var(--font-mono)', 
              fontSize: 11, 
              color: 'var(--accent-amber)',
              letterSpacing: '0.10em'
            }}>
              ANALYSIS REPORTS
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={handleExportAll}
                disabled={filteredReports.length === 0}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  padding: '4px 10px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-secondary)',
                  cursor: filteredReports.length === 0 ? 'not-allowed' : 'pointer',
                  letterSpacing: '0.05em',
                  opacity: filteredReports.length === 0 ? 0.5 : 1
                }}
              >
                ⬇ EXPORT ALL
              </button>
              <button
                onClick={loadReports}
                disabled={isLoading}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  padding: '4px 10px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-secondary)',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  letterSpacing: '0.05em',
                  opacity: isLoading ? 0.5 : 1
                }}
              >
                {isLoading ? 'LOADING...' : '↻ REFRESH'}
              </button>
            </div>
          </div>
          
          {/* Filter */}
          <input
            type="text"
            placeholder="Filter by equipment..."
            value={filterEquipment}
            onChange={(e) => setFilterEquipment(e.target.value)}
            style={{
              width: '100%',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              padding: '8px 12px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          />
        </div>

        {/* Reports List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          {error && (
            <div style={{ 
              padding: '12px',
              color: 'var(--status-critical)',
              fontFamily: 'var(--font-mono)',
              fontSize: 11
            }}>
              {error}
            </div>
          )}
          
          {filteredReports.length === 0 && !error && (
            <div style={{ 
              padding: '20px',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-sans)',
              fontSize: 13
            }}>
              No reports found. Run equipment analysis to generate reports.
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {filteredReports.map((report) => {
              const reportId = report.report_id || report.incident_summary?.incident_id
              const isHighlighted = selectedReportId === reportId
              return (
                <ReportCard
                  key={reportId}
                  report={report}
                  reportId={reportId}
                  isSelected={selectedReport?.report_id === reportId}
                  isHighlighted={isHighlighted}
                  onClick={() => handleReportClick(reportId)}
                  onExport={() => handleExportReport(report)}
                />
              )
            })}
          </div>
        </div>
      </div>

      {/* Report Detail */}
      <div style={{ 
        flex: 1, 
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {selectedReport ? (
          <ReportDetail report={selectedReport} onClose={() => setSelectedReport(null)} />
        ) : (
          <div style={{ 
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-sans)',
            fontSize: 13
          }}>
            Select a report to view details
          </div>
        )}
      </div>
    </div>
  )
}

function ReportCard({ report, reportId, isSelected, isHighlighted, onClick, onExport }) {
  const timestamp = new Date(report.incident_summary?.timestamp || report.generated_at)
  const formattedDate = timestamp.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })

  const incidentId = report.incident_summary?.incident_id || report.report_id || ''
  const equipmentName = report.incident_summary?.equipment_name || 'Unknown Equipment'
  const equipmentId = report.incident_summary?.equipment_id || ''
  const riskLevel = report.risk_assessment?.risk_level || 'MEDIUM'
  const rootCause = report.diagnosis?.root_cause || 'No diagnosis available'

  return (
    <div
      id={`report-${reportId}`}
      style={{
        background: isSelected 
          ? 'var(--bg-surface-2)' 
          : isHighlighted 
            ? 'rgba(232, 188, 93, 0.1)' 
            : 'var(--bg-surface)',
        border: `1px solid ${isSelected ? 'var(--accent-amber)' : isHighlighted ? 'var(--accent-amber)' : 'var(--border)'}`,
        borderRadius: 'var(--radius-md)',
        borderLeft: isHighlighted ? '3px solid var(--accent-amber)' : '3px solid transparent',
        padding: '12px 14px',
        cursor: 'pointer',
        transition: 'all 0.3s',
        position: 'relative'
      }}
      onMouseEnter={(e) => {
        if (!isSelected && !isHighlighted) e.currentTarget.style.borderColor = 'var(--border-active)'
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.borderColor = isHighlighted ? 'var(--accent-amber)' : 'var(--border)'
        }
      }}
    >
      <div onClick={onClick}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          marginBottom: 6
        }}>
          <div style={{ 
            fontFamily: 'var(--font-mono)', 
            fontSize: 12, 
            color: 'var(--text-primary)',
            fontWeight: 600
          }}>
            {equipmentName}
          </div>
          <RiskBadge level={riskLevel} />
        </div>

        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 10, 
          color: 'var(--text-secondary)',
          marginBottom: 4
        }}>
          {equipmentId} • #{incidentId.substring(0, 8)}
        </div>

        <div style={{ 
          fontFamily: 'var(--font-sans)', 
          fontSize: 12, 
          color: 'var(--text-secondary)',
          marginBottom: 6,
          lineHeight: 1.4,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden'
        }}>
          {rootCause}
        </div>

        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 10, 
          color: 'var(--text-muted)'
        }}>
          {formattedDate}
        </div>
      </div>
      
      {/* Export button */}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onExport()
        }}
        style={{
          position: 'absolute',
          bottom: 8,
          right: 8,
          fontFamily: 'var(--font-mono)',
          fontSize: 9,
          padding: '3px 8px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
          letterSpacing: '0.05em',
          opacity: 0.7
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.opacity = '1'
          e.currentTarget.style.borderColor = 'var(--accent-amber)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.opacity = '0.7'
          e.currentTarget.style.borderColor = 'var(--border)'
        }}
      >
        ⬇ JSON
      </button>
    </div>
  )
}

function RiskBadge({ level }) {
  const colors = {
    CRITICAL: { bg: 'rgba(232, 93, 93, 0.15)', border: 'var(--status-critical)', text: 'var(--status-critical)' },
    HIGH: { bg: 'rgba(232, 145, 93, 0.15)', border: '#e89143', text: '#e89143' },
    MEDIUM: { bg: 'rgba(232, 188, 93, 0.15)', border: 'var(--accent-amber)', text: 'var(--accent-amber)' },
    LOW: { bg: 'rgba(93, 232, 145, 0.15)', border: 'var(--status-ok)', text: 'var(--status-ok)' },
  }

  const style = colors[level] || colors.MEDIUM

  return (
    <span style={{
      fontFamily: 'var(--font-mono)',
      fontSize: 9,
      padding: '2px 6px',
      borderRadius: 'var(--radius-sm)',
      background: style.bg,
      color: style.text,
      border: `1px solid ${style.border}`,
      letterSpacing: '0.05em'
    }}>
      {level}
    </span>
  )
}

function ReportDetail({ report, onClose }) {
  const timestamp = new Date(report.generated_at || report.incident_summary?.timestamp)
  const formattedDate = timestamp.toLocaleString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  const incident = report.incident_summary || {}
  const diagnosis = report.diagnosis || {}
  const risk = report.risk_assessment || {}
  const maintenance = report.maintenance_plan || {}

  return (
    <div style={{ 
      flex: 1, 
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{ 
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <div style={{ 
            fontFamily: 'var(--font-mono)', 
            fontSize: 11, 
            color: 'var(--accent-amber)',
            letterSpacing: '0.10em',
            marginBottom: 4
          }}>
            ANALYSIS REPORT
          </div>
          <div style={{ 
            fontFamily: 'var(--font-sans)', 
            fontSize: 16, 
            color: 'var(--text-primary)',
            fontWeight: 600
          }}>
            {incident.equipment_name || 'Equipment'}
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            padding: '6px 12px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            letterSpacing: '0.05em'
          }}
        >
          CLOSE
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
        {/* Metadata */}
        <div style={{ marginBottom: 20 }}>
          <InfoRow label="Equipment ID" value={incident.equipment_id || 'N/A'} />
          <InfoRow label="Incident ID" value={incident.incident_id || 'N/A'} />
          <InfoRow label="Generated" value={formattedDate} />
          <InfoRow 
            label="Risk Level" 
            value={
              <RiskBadge level={risk.risk_level || 'MEDIUM'} />
            } 
          />
        </div>

        {/* Root Cause */}
        <Section title="ROOT CAUSE ANALYSIS">
          <div style={{ 
            color: 'var(--text-primary)', 
            fontSize: 14,
            marginBottom: 8,
            fontWeight: 600
          }}>
            {diagnosis.root_cause || 'No diagnosis available'}
          </div>
          <div style={{ 
            color: 'var(--text-secondary)', 
            fontSize: 13,
            lineHeight: 1.7,
            marginBottom: 8
          }}>
            {diagnosis.fault_description || 'No description available'}
          </div>
          {diagnosis.confidence_score !== undefined && (
            <div style={{ 
              fontFamily: 'var(--font-mono)', 
              fontSize: 11, 
              color: 'var(--text-secondary)'
            }}>
              Confidence: {(diagnosis.confidence_score * 100).toFixed(0)}%
            </div>
          )}
        </Section>

        {/* Risk Assessment */}
        <Section title="RISK ASSESSMENT">
          {risk.urgency_hours !== undefined && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                Action required within: <strong style={{ color: 'var(--text-primary)' }}>{risk.urgency_hours.toFixed(1)} hours</strong>
              </span>
            </div>
          )}
          {risk.rul_hours && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                Remaining useful life: <strong style={{ color: 'var(--text-primary)' }}>{risk.rul_hours.toFixed(1)} hours</strong>
              </span>
            </div>
          )}
          {risk.parts_required && risk.parts_required.length > 0 && (
            <div>
              <div style={{ 
                fontFamily: 'var(--font-mono)', 
                fontSize: 10, 
                color: 'var(--text-secondary)',
                marginBottom: 4
              }}>
                REQUIRED PARTS:
              </div>
              <ul style={{ 
                margin: 0, 
                paddingLeft: 20, 
                color: 'var(--text-primary)', 
                fontSize: 13 
              }}>
                {risk.parts_required.map((part, i) => (
                  <li key={i}>{part}</li>
                ))}
              </ul>
              <div style={{ 
                fontSize: 12, 
                color: risk.parts_available ? 'var(--status-ok)' : 'var(--status-warn)',
                marginTop: 4
              }}>
                {risk.parts_available ? '✓ Parts available in stock' : '⚠ Parts not available - order required'}
              </div>
            </div>
          )}
        </Section>

        {/* Immediate Actions */}
        {maintenance.immediate_actions && maintenance.immediate_actions.length > 0 && (
          <Section title="IMMEDIATE ACTIONS">
            <ol style={{ 
              margin: 0, 
              paddingLeft: 20, 
              color: 'var(--text-primary)', 
              fontSize: 13,
              lineHeight: 1.7
            }}>
              {maintenance.immediate_actions.map((action, i) => (
                <li key={i} style={{ marginBottom: 6 }}>{action}</li>
              ))}
            </ol>
          </Section>
        )}

        {/* Repair Steps */}
        {maintenance.repair_steps && maintenance.repair_steps.length > 0 && (
          <Section title="REPAIR PROCEDURE">
            <ol style={{ 
              margin: 0, 
              paddingLeft: 20, 
              color: 'var(--text-primary)', 
              fontSize: 13,
              lineHeight: 1.7
            }}>
              {maintenance.repair_steps.map((step, i) => (
                <li key={i} style={{ marginBottom: 6 }}>{step}</li>
              ))}
            </ol>
          </Section>
        )}

        {/* Long-term Recommendations */}
        {maintenance.long_term_recommendations && maintenance.long_term_recommendations.length > 0 && (
          <Section title="LONG-TERM RECOMMENDATIONS">
            <ul style={{ 
              margin: 0, 
              paddingLeft: 20, 
              color: 'var(--text-primary)', 
              fontSize: 13,
              lineHeight: 1.7
            }}>
              {maintenance.long_term_recommendations.map((rec, i) => (
                <li key={i} style={{ marginBottom: 6 }}>{rec}</li>
              ))}
            </ul>
          </Section>
        )}

        {/* Evidence */}
        {diagnosis.evidence_sources && diagnosis.evidence_sources.length > 0 && (
          <Section title="EVIDENCE FROM KNOWLEDGE BASE">
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: 6 
            }}>
              {diagnosis.evidence_sources.map((ref, i) => {
                // evidence_sources can be either string refs ["[C1]", "[C2]"] 
                // or full citation objects [{ref: "[C1]", doc_id: "...", ...}]
                const isFullCitation = typeof ref === 'object' && ref !== null
                
                if (isFullCitation) {
                  // Use CitationTag for full citation objects
                  return <CitationTag key={i} citation={ref} />
                } else {
                  // Fallback for string refs (legacy format)
                  return (
                    <span
                      key={i}
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: 11,
                        padding: '4px 8px',
                        background: 'var(--accent-amber-glow)',
                        border: '1px solid var(--accent-amber-dim)',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--accent-amber)',
                      }}
                    >
                      {ref}
                    </span>
                  )
                }
              })}
            </div>
          </Section>
        )}

        {/* Sensor Data */}
        {report.sensor_data && Object.keys(report.sensor_data).length > 0 && (
          <Section title="SENSOR READINGS">
            <div style={{ 
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--text-secondary)'
            }}>
              {Object.entries(report.sensor_data).map(([key, value]) => (
                <div key={key} style={{ marginBottom: 4 }}>
                  <span style={{ color: 'var(--text-muted)' }}>{key}:</span>{' '}
                  <span style={{ color: 'var(--text-primary)' }}>{value}</span>
                </div>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ 
        fontFamily: 'var(--font-mono)', 
        fontSize: 10, 
        color: 'var(--accent-amber)',
        letterSpacing: '0.08em',
        marginBottom: 10
      }}>
        {title}
      </div>
      {children}
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div style={{ 
      display: 'flex', 
      marginBottom: 8,
      fontSize: 13
    }}>
      <div style={{ 
        flex: '0 0 150px',
        fontFamily: 'var(--font-mono)', 
        fontSize: 11,
        color: 'var(--text-secondary)'
      }}>
        {label}:
      </div>
      <div style={{ 
        flex: 1,
        fontFamily: 'var(--font-mono)', 
        fontSize: 11,
        color: 'var(--text-primary)'
      }}>
        {value}
      </div>
    </div>
  )
}
