import React from 'react'
import StatusDot from '../shared/StatusDot'
import { formatSensorValue } from '../../utils/formatters'

export default function EquipmentCard({ equip, backendLog, isSelected, onClick }) {
  if (!equip) return null

  // Use backend severity if available, otherwise fall back to frontend status
  const backendSeverity = backendLog?.severity
  const isCritical = backendSeverity === 'CRITICAL' || backendSeverity === 'WARNING' || equip.status === 'critical'
  const displayStatus = backendSeverity || (equip.status === 'critical' ? 'CRITICAL' : 'NORMAL')

  // Pick the 3 key sensor values to show
  const sensorKeys = Object.keys(equip.sensors || {}).slice(0, 3)

  return (
    <button
      onClick={onClick}
      style={{
        background: 'var(--bg-surface)',
        border: `1px solid ${isCritical ? 'var(--status-critical)' : isSelected ? 'var(--border-active)' : 'var(--border)'}`,
        borderRadius: 'var(--radius-md)',
        padding: '10px 12px',
        cursor: 'pointer',
        textAlign: 'left',
        position: 'relative',
        overflow: 'hidden',
        transition: 'border-color var(--transition)',
        boxShadow: isCritical ? '0 0 0 1px var(--status-critical)' : isSelected ? '0 0 0 1px var(--border-active)' : 'none',
        width: '100%',
      }}
    >
      {/* Critical pulse line at top */}
      {isCritical && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 2,
            background: 'var(--status-critical)',
            animation: 'topLinePulse 1s ease-in-out infinite',
          }}
        />
      )}

      {/* Top row: name + status dot */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: isCritical ? 'var(--status-critical)' : 'var(--text-primary)',
            fontWeight: 500,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            flex: 1,
            marginRight: 6,
          }}
        >
          {equip.name}
        </span>
        <StatusDot status={equip.status === 'critical' ? 'critical' : 'ok'} size="small" />
      </div>

      {/* Status row: backend severity + fault code */}
      <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: displayStatus === 'CRITICAL' ? 'var(--status-critical)' : displayStatus === 'WARNING' ? 'var(--accent-amber)' : 'var(--status-ok)',
            letterSpacing: '0.04em',
          }}
        >
          {displayStatus}
        </span>
        {backendLog?.fault_code && backendLog.fault_code !== '—' && (
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--text-muted)',
              letterSpacing: '0.02em',
            }}
          >
            {backendLog.fault_code}
          </span>
        )}
      </div>

      {/* Sensor values from backend log if available, otherwise frontend */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {backendLog ? (
          <>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: backendLog.anomaly_sensors?.includes('vibration_mm_s') ? 'var(--status-critical)' : 'var(--text-secondary)', letterSpacing: '0.02em' }}>
              VIB {backendLog.vibration_mm_s?.toFixed(1)}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: backendLog.anomaly_sensors?.includes('bearing_temp_c') ? 'var(--status-critical)' : 'var(--text-secondary)', letterSpacing: '0.02em' }}>
              TMP {backendLog.bearing_temp_c?.toFixed(1)}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: backendLog.anomaly_sensors?.includes('motor_current_a') ? 'var(--status-critical)' : 'var(--text-secondary)', letterSpacing: '0.02em' }}>
              CUR {backendLog.motor_current_a?.toFixed(1)}
            </span>
          </>
        ) : (
          sensorKeys.map((key) => {
            const sensor = equip.sensors[key]
            const val = sensor?.latestValue
            const isAnom = sensor?.isAnomaly
            return (
              <span
                key={key}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  color: isAnom ? 'var(--status-critical)' : 'var(--text-secondary)',
                  letterSpacing: '0.02em',
                  animation: 'countUp 0.3s ease',
                }}
              >
                {key.slice(0, 3).toUpperCase()} {val !== null ? val?.toFixed(1) : '--'}
              </span>
            )
          })
        )}
      </div>
    </button>
  )
}
