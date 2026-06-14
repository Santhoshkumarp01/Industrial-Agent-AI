/**
 * AgentStreamingStatus - Shows real-time progress of 3-agent analysis
 * 
 * Displays live updates as agents run:
 * 🔍 Agent 1: Analyzing root cause...
 * ✅ Agent 1: Root cause identified
 * ⚠️ Agent 2: Assessing risk level...
 * etc.
 */
import React from 'react'

export default function AgentStreamingStatus({ updates }) {
  if (!updates || updates.length === 0) return null

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      padding: '12px',
      marginBottom: '12px',
    }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--accent-blue)',
        letterSpacing: '0.08em',
        marginBottom: 10,
        textTransform: 'uppercase'
      }}>
        🤖 Multi-Agent Analysis in Progress
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {updates.map((update, index) => (
          <AgentUpdate key={index} update={update} />
        ))}
      </div>
    </div>
  )
}

function AgentUpdate({ update }) {
  const { type, agent, status, message, data } = update

  // Determine styling based on status
  const getStyles = () => {
    if (status === 'complete') {
      return {
        icon: '✅',
        color: 'var(--status-success)',
        opacity: 1
      }
    } else if (status === 'starting' || status === 'running') {
      return {
        icon: '⏳',
        color: 'var(--accent-blue)',
        opacity: 0.9
      }
    } else {
      return {
        icon: '⚪',
        color: 'var(--text-muted)',
        opacity: 0.7
      }
    }
  }

  const styles = getStyles()

  // Show collapsible data for completed agents
  const [expanded, setExpanded] = React.useState(false)
  const hasData = data && Object.keys(data).length > 0 && type === 'agent_complete'

  return (
    <div style={{
      borderLeft: `2px solid ${styles.color}`,
      paddingLeft: 10,
      opacity: styles.opacity
    }}>
      {/* Main message */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: hasData ? 4 : 0
      }}>
        <span style={{ fontSize: 12 }}>{styles.icon}</span>
        <span style={{
          fontFamily: 'var(--font-sans)',
          fontSize: 12,
          color: 'var(--text-primary)',
          flex: 1
        }}>
          {message}
        </span>
        
        {hasData && (
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent-blue)',
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              cursor: 'pointer',
              padding: '2px 6px'
            }}
          >
            {expanded ? '▼' : '▶'}
          </button>
        )}
      </div>

      {/* Expanded data (for completed agents) */}
      {hasData && expanded && (
        <div style={{
          marginTop: 6,
          padding: 8,
          background: 'var(--bg-base)',
          borderRadius: 'var(--radius-sm)',
          fontSize: 11,
          fontFamily: 'var(--font-mono)'
        }}>
          {agent === 'root_cause' && data && (
            <>
              <div style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>
                <strong>Root Cause:</strong> {data.root_cause?.substring(0, 100)}...
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 10 }}>
                Confidence: {Math.round(data.confidence * 100)}% | Evidence: {data.evidence?.length || 0} sources
              </div>
            </>
          )}

          {agent === 'risk' && data && (
            <>
              <div style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>
                <strong>Risk Level:</strong> <span style={{
                  color: data.risk_level === 'CRITICAL' ? 'var(--status-critical)' : 
                        data.risk_level === 'HIGH' ? 'var(--status-warning)' : 
                        'var(--status-success)'
                }}>{data.risk_level}</span>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 10 }}>
                Urgency: {data.urgency_hours}h | Parts Required: {data.parts_required?.length || 0}
              </div>
            </>
          )}

          {agent === 'maintenance' && data && (
            <>
              <div style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>
                <strong>Actions:</strong> {data.immediate_actions?.length || 0} immediate, {data.repair_steps?.length || 0} repair steps
              </div>
              {data.immediate_actions?.slice(0, 2).map((action, i) => (
                <div key={i} style={{ color: 'var(--text-muted)', fontSize: 10, marginTop: 2 }}>
                  • {action.substring(0, 60)}...
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}
