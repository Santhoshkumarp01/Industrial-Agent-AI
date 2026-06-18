import React from 'react'
import { trackUserRole } from '../../utils/analytics'

const ROLES = [
  {
    id: 'engineer',
    title: 'Maintenance Engineer',
    description: 'Full system access for maintenance operations',
    features: ['AI Chat & Analysis', 'Document Upload', 'Anomaly Detection', 'Report Management'],
    icon: '🔧',
    color: 'var(--accent-blue)',
  },
  {
    id: 'manager',
    title: 'Plant Manager',
    description: 'View-only access for oversight and reporting',
    features: ['View Reports', 'Monitor Equipment', 'Review Logbook', 'Analytics Dashboard'],
    icon: '📊',
    color: 'var(--accent-amber)',
  },
  {
    id: 'technician',
    title: 'Field Technician',
    description: 'Limited access for field operations',
    features: ['View Monitoring', 'Update Logbook', 'View Analysis', 'Equipment Status'],
    icon: '👷',
    color: 'var(--status-ok)',
  },
  {
    id: 'judge',
    title: 'Judge / Demo',
    description: 'Complete access for evaluation and testing',
    features: ['All Features Enabled', 'Demo Scenarios', 'Full Documentation', 'Test Environment'],
    icon: '🎯',
    color: '#B388FF',
  },
]

export default function RoleLanding({ onSelectRole }) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-base)',
      padding: '20px',
    }}>
      <div style={{
        maxWidth: 1100,
        width: '100%',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <h1 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 32,
            color: 'var(--text-primary)',
            letterSpacing: '0.02em',
            marginBottom: 12,
            fontWeight: 600,
          }}>
            Industrial Agent AI
          </h1>
          <p style={{
            fontFamily: 'var(--font-sans)',
            fontSize: 15,
            color: 'var(--text-secondary)',
            maxWidth: 500,
            margin: '0 auto',
            lineHeight: 1.6,
          }}>
            AI-powered steel plant maintenance intelligence system with role-based access control
          </p>
        </div>

        {/* Role selection text */}
        <div style={{
          textAlign: 'center',
          marginBottom: 32,
        }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--text-muted)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}>
            Select Your Role to Continue
          </span>
        </div>

        {/* Role cards grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: 20,
          marginBottom: 40,
        }}>
          {ROLES.map((role) => (
            <RoleCard
              key={role.id}
              role={role}
              onSelect={() => {
                // Track role selection
                trackUserRole(role.id)
                onSelectRole(role.id)
              }}
            />
          ))}
        </div>

        {/* Footer info */}
        <div style={{
          textAlign: 'center',
          padding: '20px',
          borderTop: '1px solid var(--border)',
        }}>
          <p style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-muted)',
            letterSpacing: '0.04em',
          }}>
            Powered by Phi-3.5 Fine-tuned LLM • Hybrid RAG • Multi-Agent System
          </p>
        </div>
      </div>
    </div>
  )
}

function RoleCard({ role, onSelect }) {
  const [isHovered, setIsHovered] = React.useState(false)

  return (
    <button
      onClick={onSelect}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: isHovered ? 'var(--bg-surface-2)' : 'var(--bg-surface)',
        border: `1px solid ${isHovered ? role.color : 'var(--border)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'var(--transition)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Glow effect on hover */}
      {isHovered && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 2,
          background: role.color,
          boxShadow: `0 0 20px ${role.color}`,
        }} />
      )}

      {/* Icon */}
      <div style={{
        fontSize: 32,
        marginBottom: 16,
        filter: isHovered ? 'none' : 'grayscale(0.3)',
        transition: 'var(--transition)',
      }}>
        {role.icon}
      </div>

      {/* Title */}
      <h3 style={{
        fontFamily: 'var(--font-sans)',
        fontSize: 16,
        color: isHovered ? role.color : 'var(--text-primary)',
        marginBottom: 8,
        fontWeight: 600,
        transition: 'var(--transition)',
      }}>
        {role.title}
      </h3>

      {/* Description */}
      <p style={{
        fontFamily: 'var(--font-sans)',
        fontSize: 12,
        color: 'var(--text-secondary)',
        lineHeight: 1.5,
        marginBottom: 16,
      }}>
        {role.description}
      </p>

      {/* Features */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
      }}>
        {role.features.map((feature, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <div style={{
              width: 4,
              height: 4,
              borderRadius: '50%',
              background: isHovered ? role.color : 'var(--border-active)',
              transition: 'var(--transition)',
            }} />
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--text-muted)',
              letterSpacing: '0.02em',
            }}>
              {feature}
            </span>
          </div>
        ))}
      </div>

      {/* Select button */}
      <div style={{
        marginTop: 20,
        paddingTop: 16,
        borderTop: '1px solid var(--border)',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: isHovered ? role.color : 'var(--text-muted)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          transition: 'var(--transition)',
        }}>
          Select Role →
        </span>
      </div>
    </button>
  )
}
