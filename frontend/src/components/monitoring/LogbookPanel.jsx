import React, { useState, useEffect } from 'react'
import { getLogbook, getLogbookEntry } from '../../services/api'
import { formatTimestamp } from '../../utils/formatters'
import RiskBadge from '../shared/RiskBadge'
import Spinner from '../shared/Spinner'
import useAppStore from '../../store/appStore'

export default function LogbookPanel() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedEntry, setSelectedEntry] = useState(null)
  const [equipmentFilter, setEquipmentFilter] = useState('')
  const [uniqueEquipment, setUniqueEquipment] = useState([])
  
  // Get selected entry from store
  const selectedLogbookEntryId = useAppStore((s) => s.selectedLogbookEntryId)
  const clearLogbookSelection = useAppStore((s) => s.clearLogbookSelection)

  useEffect(() => {
    fetchLogbook()
  }, [equipmentFilter])
  
  // Auto-open selected entry from store
  useEffect(() => {
    if (selectedLogbookEntryId && entries.length > 0) {
      const entry = entries.find(e => e.id === selectedLogbookEntryId)
      if (entry) {
        handleRowClick(entry)
        // Scroll to the entry
        setTimeout(() => {
          const element = document.getElementById(`logbook-entry-${selectedLogbookEntryId}`)
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }, 100)
        // Clear selection after 5 seconds
        setTimeout(() => clearLogbookSelection(), 5000)
      }
    }
  }, [selectedLogbookEntryId, entries])

  const fetchLogbook = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getLogbook(equipmentFilter || null, 100)
      setEntries(data.entries || [])
      
      // Extract unique equipment names
      const equipment = [...new Set((data.entries || []).map(e => e.equipment_name))]
      setUniqueEquipment(equipment)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRowClick = async (entry) => {
    if (selectedEntry?.id === entry.id) {
      setSelectedEntry(null)
      return
    }

    try {
      const fullEntry = await getLogbookEntry(entry.id)
      setSelectedEntry(fullEntry)
    } catch (err) {
      console.error('Failed to fetch full entry:', err)
      setSelectedEntry(entry)
    }
  }

  const isNewEntry = (timestamp) => {
    const entryTime = new Date(timestamp)
    const now = new Date()
    const hoursDiff = (now - entryTime) / (1000 * 60 * 60)
    return hoursDiff < 1
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%'
      }}>
        <Spinner />
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: 'var(--bg-surface-1)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid var(--border-subtle)'
      }}>
        <h2 style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 14,
          color: 'var(--accent-amber)',
          margin: 0,
          letterSpacing: '0.1em',
          marginBottom: 12
        }}>
          📋 MAINTENANCE LOGBOOK
        </h2>
        
        {/* Equipment Filter */}
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select
            value={equipmentFilter}
            onChange={(e) => setEquipmentFilter(e.target.value)}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-active)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-primary)',
              cursor: 'pointer'
            }}
          >
            <option value="">All Equipment</option>
            {uniqueEquipment.map(eq => (
              <option key={eq} value={eq}>{eq}</option>
            ))}
          </select>
          
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--text-secondary)'
          }}>
            {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
          </span>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          color: 'var(--status-critical)'
        }}>
          Error: {error}
        </div>
      )}

      {/* Empty State */}
      {!error && entries.length === 0 && (
        <div style={{
          padding: '40px 20px',
          textAlign: 'center',
          color: 'var(--text-muted)'
        }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📋</div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            letterSpacing: '0.08em'
          }}>
            No logbook entries yet
          </div>
        </div>
      )}

      {/* Logbook Table */}
      {!error && entries.length > 0 && (
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '20px 24px'
        }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontFamily: 'var(--font-sans)',
            fontSize: 13
          }}>
            <thead>
              <tr style={{
                borderBottom: '2px solid var(--border-active)',
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--text-secondary)',
                letterSpacing: '0.08em'
              }}>
                <th style={{ textAlign: 'left', padding: '8px 12px 8px 0' }}>EQUIPMENT</th>
                <th style={{ textAlign: 'left', padding: '8px 12px' }}>TIMESTAMP</th>
                <th style={{ textAlign: 'left', padding: '8px 12px' }}>ROOT CAUSE</th>
                <th style={{ textAlign: 'center', padding: '8px 12px' }}>RISK</th>
                <th style={{ textAlign: 'center', padding: '8px 12px' }}>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => {
                const isHighlighted = selectedLogbookEntryId === entry.id
                return (
                <React.Fragment key={entry.id}>
                  <tr
                    id={`logbook-entry-${entry.id}`}
                    onClick={() => handleRowClick(entry)}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      background: selectedEntry?.id === entry.id 
                        ? 'var(--bg-surface-2)' 
                        : isHighlighted 
                          ? 'rgba(232, 188, 93, 0.1)' 
                          : 'transparent',
                      borderLeft: isHighlighted ? '3px solid var(--accent-amber)' : '3px solid transparent',
                      transition: 'all 0.3s'
                    }}
                    onMouseEnter={(e) => {
                      if (selectedEntry?.id !== entry.id && !isHighlighted) {
                        e.currentTarget.style.background = 'var(--bg-surface-2)'
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedEntry?.id !== entry.id) {
                        e.currentTarget.style.background = isHighlighted ? 'rgba(232, 188, 93, 0.1)' : 'transparent'
                      }
                    }}
                  >
                    <td style={{ padding: '12px 12px 12px 0' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <strong style={{ color: 'var(--text-primary)' }}>
                          {entry.equipment_name}
                        </strong>
                        {isNewEntry(entry.timestamp) && (
                          <span style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: 9,
                            padding: '2px 6px',
                            borderRadius: 'var(--radius-sm)',
                            background: 'var(--accent-amber-glow)',
                            color: 'var(--accent-amber)',
                            letterSpacing: '0.06em'
                          }}>
                            NEW
                          </span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>
                      {formatTimestamp(entry.timestamp)}
                    </td>
                    <td style={{ padding: '12px', color: 'var(--text-primary)' }}>
                      {entry.root_cause || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <RiskBadge level={entry.risk_level} />
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: 10,
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-sm)',
                        background: entry.resolved ? 'rgba(93, 232, 145, 0.15)' : 'rgba(232, 188, 93, 0.15)',
                        color: entry.resolved ? 'var(--status-ok)' : 'var(--accent-amber)',
                        border: `1px solid ${entry.resolved ? 'var(--status-ok)' : 'var(--accent-amber)'}`,
                        letterSpacing: '0.06em'
                      }}>
                        {entry.resolved ? '✓ RESOLVED' : 'OPEN'}
                      </span>
                    </td>
                  </tr>
                  
                  {/* Expanded Row Details */}
                  {selectedEntry?.id === entry.id && (
                    <tr>
                      <td colSpan={5} style={{ padding: 0 }}>
                        <div style={{
                          background: 'var(--bg-surface-3)',
                          border: '1px solid var(--border-active)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '16px',
                          margin: '8px 0'
                        }}>
                          {/* Incident Details */}
                          <div style={{ marginBottom: 16 }}>
                            <div style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: 10,
                              color: 'var(--accent-amber)',
                              letterSpacing: '0.08em',
                              marginBottom: 8
                            }}>
                              INCIDENT DETAILS
                            </div>
                            <div style={{ color: 'var(--text-primary)', fontSize: 13, lineHeight: 1.7 }}>
                              <p style={{ margin: '0 0 8px 0' }}>
                                <strong>Alert:</strong> {selectedEntry.alert_description || 'N/A'}
                              </p>
                              <p style={{ margin: '0 0 8px 0' }}>
                                <strong>Fault:</strong> {selectedEntry.fault_description || 'N/A'}
                              </p>
                              {selectedEntry.rul_hours && (
                                <p style={{ margin: '0 0 8px 0' }}>
                                  <strong>RUL:</strong> {selectedEntry.rul_hours.toFixed(1)} hours
                                </p>
                              )}
                            </div>
                          </div>

                          {/* Immediate Actions */}
                          {selectedEntry.immediate_actions && selectedEntry.immediate_actions.length > 0 && (
                            <div style={{ marginBottom: 16 }}>
                              <div style={{
                                fontFamily: 'var(--font-mono)',
                                fontSize: 10,
                                color: 'var(--accent-amber)',
                                letterSpacing: '0.08em',
                                marginBottom: 8
                              }}>
                                IMMEDIATE ACTIONS
                              </div>
                              <ol style={{
                                margin: 0,
                                paddingLeft: 20,
                                color: 'var(--text-primary)',
                                fontSize: 13,
                                lineHeight: 1.7
                              }}>
                                {selectedEntry.immediate_actions.map((action, i) => (
                                  <li key={i} style={{ marginBottom: 4 }}>{action}</li>
                                ))}
                              </ol>
                            </div>
                          )}

                          {/* Feedback */}
                          {selectedEntry.feedback && selectedEntry.feedback.length > 0 && (
                            <div style={{ marginBottom: 16 }}>
                              <div style={{
                                fontFamily: 'var(--font-mono)',
                                fontSize: 10,
                                color: 'var(--accent-amber)',
                                letterSpacing: '0.08em',
                                marginBottom: 8
                              }}>
                                ENGINEER FEEDBACK
                              </div>
                              {selectedEntry.feedback.map((fb, i) => (
                                <div key={i} style={{
                                  background: fb.verdict === 'confirmed' 
                                    ? 'rgba(93, 232, 145, 0.1)' 
                                    : 'rgba(232, 93, 93, 0.1)',
                                  border: `1px solid ${fb.verdict === 'confirmed' ? 'var(--status-ok)' : 'var(--status-critical)'}`,
                                  borderRadius: 'var(--radius-sm)',
                                  padding: '10px',
                                  marginBottom: 8
                                }}>
                                  <div style={{
                                    fontFamily: 'var(--font-mono)',
                                    fontSize: 10,
                                    color: fb.verdict === 'confirmed' ? 'var(--status-ok)' : 'var(--status-critical)',
                                    marginBottom: 6,
                                    letterSpacing: '0.06em'
                                  }}>
                                    {fb.verdict === 'confirmed' ? '✓ CONFIRMED' : '✗ INCORRECT'} 
                                    {' by '}{fb.engineer_name}
                                  </div>
                                  {fb.actual_root_cause && (
                                    <p style={{ margin: '4px 0', fontSize: 12, color: 'var(--text-primary)' }}>
                                      <strong>Actual cause:</strong> {fb.actual_root_cause}
                                    </p>
                                  )}
                                  {fb.actual_action_taken && (
                                    <p style={{ margin: '4px 0', fontSize: 12, color: 'var(--text-primary)' }}>
                                      <strong>Action taken:</strong> {fb.actual_action_taken}
                                    </p>
                                  )}
                                  {fb.outcome && (
                                    <p style={{ margin: '4px 0', fontSize: 12, color: 'var(--text-secondary)' }}>
                                      <strong>Outcome:</strong> {fb.outcome}
                                    </p>
                                  )}
                                  {fb.downtime_hours !== null && fb.downtime_hours !== undefined && (
                                    <p style={{ margin: '4px 0', fontSize: 12, color: 'var(--text-secondary)' }}>
                                      <strong>Downtime:</strong> {fb.downtime_hours.toFixed(1)}h
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )})}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
