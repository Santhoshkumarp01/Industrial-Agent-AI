/**
 * AgentStreamingStatus - Shows real-time progress of 3-agent analysis
 * 
 * Professional display similar to Claude's artifact thinking:
 * - Clean, minimal design
 * - Clear agent progression
 * - Expandable details
 */
import React from 'react'

export default function AgentStreamingStatus({ updates }) {
  if (!updates || updates.length === 0) return null

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      padding: '14px 16px',
      marginBottom: '14px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 12,
        paddingBottom: 10,
        borderBottom: '1px solid var(--border-subtle)'
      }}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="var(--accent-blue)" strokeWidth="1.5" fill="none" />
          <path d="M8 4v4l3 2" stroke="var(--accent-blue)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <span style={{
          fontFamily: 'var(--font-sans)',
          fontSize: 13,
          color: 'var(--text-primary)',
          fontWeight: 500,
          letterSpacing: '-0.01em'
        }}>
          Multi-Agent Analysis
        </span>
        <div style={{
          marginLeft: 'auto',
          padding: '2px 8px',
          borderRadius: 'var(--radius-sm)',
          background: 'rgba(59, 130, 246, 0.1)',
          fontSize: 10,
          fontFamily: 'var(--font-mono)',
          color: 'var(--accent-blue)',
          letterSpacing: '0.02em'
        }}>
          IN PROGRESS
        </div>
      </div>

      {/* Agent Updates */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {updates.map((update, index) => (
          <AgentUpdate key={index} update={update} />
        ))}
      </div>
    </div>
  )
}

function AgentUpdate({ update }) {
  const { type, agent, status, message, data } = update

  // Get agent display info
  const getAgentInfo = () => {
    if (agent === 'root_cause') {
      return { number: '1', label: 'Root Cause Analysis', color: 'var(--accent-blue)' }
    } else if (agent === 'risk') {
      return { number: '2', label: 'Risk Assessment', color: 'var(--status-warning)' }
    } else if (agent === 'maintenance') {
      return { number: '3', label: 'Maintenance Planning', color: 'var(--accent-purple)' }
    }
    return null
  }

  const agentInfo = getAgentInfo()

  // Determine styling based on status
  const getStatusIcon = () => {
    if (status === 'complete') {
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" fill="var(--status-success)" opacity="0.1" />
          <path d="M5 8l2 2 4-4" stroke="var(--status-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )
    } else if (status === 'starting' || status === 'running') {
      return (
        <div style={{ 
          width: 16, 
          height: 16, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}>
          <div style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: agentInfo ? agentInfo.color : 'var(--accent-blue)',
            animation: 'pulse 1.5s ease-in-out infinite'
          }} />
          <style>{`
            @keyframes pulse {
              0%, 100% { opacity: 0.4; transform: scale(0.95); }
              50% { opacity: 1; transform: scale(1.05); }
            }
          `}</style>
        </div>
      )
    } else {
      return (
        <div style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--border)', opacity: 0.3 }} />
      )
    }
  }

  // Show collapsible data for completed agents
  const [expanded, setExpanded] = React.useState(false)
  const hasData = data && Object.keys(data).length > 0 && type === 'agent_complete'

  // Extract clean message without emoji prefixes
  const cleanMessage = message.replace(/^[🔍⚠️🔧✅💾✨🚀⏳]+\s*/, '')

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }}>
      {/* Main row */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10
      }}>
        {/* Status icon */}
        <div style={{ marginTop: 2, flexShrink: 0 }}>
          {getStatusIcon()}
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Agent label + number */}
          {agentInfo && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 2
            }}>
              <div style={{
                width: 18,
                height: 18,
                borderRadius: '50%',
                background: status === 'complete' ? agentInfo.color : 'transparent',
                border: `1.5px solid ${agentInfo.color}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 10,
                fontFamily: 'var(--font-mono)',
                color: status === 'complete' ? 'white' : agentInfo.color,
                fontWeight: 600
              }}>
                {agentInfo.number}
              </div>
              <span style={{
                fontFamily: 'var(--font-sans)',
                fontSize: 11,
                color: 'var(--text-muted)',
                fontWeight: 500,
                letterSpacing: '-0.01em'
              }}>
                {agentInfo.label}
              </span>
            </div>
          )}

          {/* Message */}
          <div style={{
            fontFamily: 'var(--font-sans)',
            fontSize: 12,
            color: status === 'complete' ? 'var(--text-primary)' : 'var(--text-secondary)',
            lineHeight: 1.4,
            paddingLeft: agentInfo ? 24 : 0
          }}>
            {cleanMessage}
          </div>
        </div>

        {/* Expand button */}
        {hasData && (
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: 4,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 'var(--radius-sm)',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-base)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
          >
            <svg 
              width="14" 
              height="14" 
              viewBox="0 0 14 14" 
              fill="none"
              style={{ 
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s'
              }}
            >
              <path d="M3.5 5.5L7 9l3.5-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        )}
      </div>

      {/* Expanded data */}
      {hasData && expanded && (
        <div style={{
          marginLeft: 26,
          marginTop: 4,
          padding: 10,
          background: 'var(--bg-base)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          fontSize: 11,
          fontFamily: 'var(--font-sans)'
        }}>
          {agent === 'root_cause' && data && (
            <>
              <div style={{ marginBottom: 8 }}>
                <div style={{ 
                  fontSize: 10, 
                  color: 'var(--text-muted)', 
                  fontWeight: 500,
                  marginBottom: 4,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Root Cause
                </div>
                <div style={{ color: 'var(--text-primary)', lineHeight: 1.5 }}>
                  {data.root_cause?.substring(0, 150)}{data.root_cause?.length > 150 ? '...' : ''}
                </div>
              </div>
              <div style={{ 
                display: 'flex', 
                gap: 12,
                paddingTop: 8,
                borderTop: '1px solid var(--border-subtle)',
                fontSize: 10,
                color: 'var(--text-muted)'
              }}>
                <span>Confidence: <strong style={{ color: 'var(--text-primary)' }}>{Math.round(data.confidence * 100)}%</strong></span>
                <span>Evidence: <strong style={{ color: 'var(--text-primary)' }}>{data.evidence?.length || 0} sources</strong></span>
                {data.similar_incidents_count > 0 && (
                  <span>Similar incidents: <strong style={{ color: 'var(--text-primary)' }}>{data.similar_incidents_count}</strong></span>
                )}
              </div>
            </>
          )}

          {agent === 'risk' && data && (
            <>
              <div style={{ marginBottom: 8 }}>
                <div style={{ 
                  fontSize: 10, 
                  color: 'var(--text-muted)', 
                  fontWeight: 500,
                  marginBottom: 4,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Risk Assessment
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 10,
                    fontWeight: 600,
                    fontFamily: 'var(--font-mono)',
                    background: data.risk_level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.1)' : 
                               data.risk_level === 'HIGH' ? 'rgba(249, 115, 22, 0.1)' : 
                               data.risk_level === 'MEDIUM' ? 'rgba(234, 179, 8, 0.1)' :
                               'rgba(34, 197, 94, 0.1)',
                    color: data.risk_level === 'CRITICAL' ? 'var(--status-critical)' : 
                          data.risk_level === 'HIGH' ? 'var(--status-warning)' : 
                          data.risk_level === 'MEDIUM' ? '#eab308' :
                          'var(--status-success)'
                  }}>
                    {data.risk_level}
                  </span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>
                    Requires action within <strong style={{ color: 'var(--text-primary)' }}>{Math.round(data.urgency_hours)}h</strong>
                  </span>
                </div>
                
                {/* RUL Display */}
                {data.rul_hours && (
                  <div style={{ 
                    padding: '6px 8px',
                    marginBottom: 8,
                    background: 'rgba(59, 130, 246, 0.05)',
                    borderLeft: '2px solid var(--accent-blue)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 11
                  }}>
                    <span style={{ color: 'var(--text-muted)' }}>Remaining Useful Life: </span>
                    <strong style={{ color: 'var(--accent-blue)' }}>
                      {data.rul_hours < 48 ? `${Math.round(data.rul_hours)}h` : `${(data.rul_hours / 24).toFixed(1)} days`}
                    </strong>
                  </div>
                )}
              </div>
              
              {/* Spare Parts Section */}
              <div style={{ 
                paddingTop: 8,
                borderTop: '1px solid var(--border-subtle)'
              }}>
                <div style={{ 
                  fontSize: 10, 
                  color: 'var(--text-muted)', 
                  fontWeight: 500,
                  marginBottom: 6,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Spare Parts Required
                </div>
                {data.parts_required && data.parts_required.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {data.parts_required.map((part, i) => {
                      const stock = data.parts_stock?.[part] || 0
                      const available = stock > 0
                      return (
                        <div key={i} style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: 8,
                          fontSize: 11,
                          color: 'var(--text-secondary)'
                        }}>
                          <span style={{ 
                            width: 14, 
                            height: 14, 
                            borderRadius: '50%', 
                            background: available ? 'var(--status-success)' : 'var(--status-warning)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 9,
                            color: 'white',
                            fontWeight: 600,
                            flexShrink: 0
                          }}>
                            {available ? '✓' : '!'}
                          </span>
                          <span style={{ flex: 1 }}>{part}</span>
                          <span style={{ 
                            fontSize: 10,
                            fontFamily: 'var(--font-mono)',
                            color: available ? 'var(--status-success)' : 'var(--status-warning)'
                          }}>
                            {available ? `Stock: ${stock}` : 'Out of stock'}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No parts required
                  </div>
                )}
              </div>
            </>
          )}

          {agent === 'maintenance' && data && (
            <>
              <div style={{ 
                fontSize: 10, 
                color: 'var(--text-muted)', 
                fontWeight: 500,
                marginBottom: 6,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                Maintenance Plan
              </div>
              <div style={{ marginBottom: 8 }}>
                <div style={{ 
                  display: 'flex', 
                  gap: 12,
                  fontSize: 10,
                  color: 'var(--text-muted)',
                  marginBottom: 8
                }}>
                  <span><strong style={{ color: 'var(--text-primary)' }}>{data.immediate_actions?.length || 0}</strong> immediate actions</span>
                  <span><strong style={{ color: 'var(--text-primary)' }}>{data.repair_steps?.length || 0}</strong> repair steps</span>
                </div>
                {data.immediate_actions?.slice(0, 2).map((action, i) => (
                  <div key={i} style={{ 
                    color: 'var(--text-secondary)', 
                    fontSize: 11, 
                    marginTop: 4,
                    paddingLeft: 12,
                    position: 'relative',
                    lineHeight: 1.4
                  }}>
                    <span style={{ 
                      position: 'absolute', 
                      left: 0, 
                      color: 'var(--accent-blue)' 
                    }}>
                      {i + 1}.
                    </span>
                    {action.substring(0, 80)}{action.length > 80 ? '...' : ''}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
