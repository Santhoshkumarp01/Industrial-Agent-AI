import React from 'react'
import EquipmentCard from './EquipmentCard'
import SensorChart from './SensorChart'
import AlertBanner from './AlertBanner'
import { formatRelativeTime } from '../../utils/formatters'
import { EQUIPMENT_LIST } from '../../services/sensorSimulator'

const SENSOR_LABELS = {
  vibration:   'Vibration (mm/s)',
  temperature: 'Bearing Temp (°C)',
  current:     'Motor Current (A)',
  pressure:    'Lube Pressure (bar)',
}

export default function MonitoringPanel({ sensorHook, onSendAlertToChat }) {
  const {
    equipmentData,
    alerts,
    selectedEquipment,
    selectEquipment,
    dismissAlert,
    triggerAnomaly,
  } = sensorHook

  const lastUpdated = new Date()
  const topAlert = alerts[0] || null
  const selectedEquip = equipmentData[selectedEquipment]

  const handleViewAnalysis = (alert) => {
    const sensorCfg = EQUIPMENT_LIST.find((e) => e.id === alert.equipmentId)
      ?.sensors?.[alert.sensorKey]
    const threshold = sensorCfg ? (sensorCfg.normal[1]).toFixed(1) : 'N/A'
    const query =
      `ALERT: Vibration anomaly detected on ${alert.equipmentName}. ` +
      `${alert.sensorKey} reading: ${alert.value?.toFixed(1)} ` +
      `(threshold: ${threshold}). Please analyze and recommend action.`
    onSendAlertToChat(query)
    dismissAlert(alert.id)
  }

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minWidth: 0,
      }}
    >
      {/* Panel header */}
      <div
        style={{
          height: 44,
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          flexShrink: 0,
        }}
      >
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.08em' }}>
          LIVE MONITOR
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          UPDATED {formatRelativeTime(lastUpdated).toUpperCase()}
        </span>
      </div>

      {/* Alert banner */}
      {topAlert && (
        <AlertBanner
          alert={topAlert}
          onDismiss={dismissAlert}
          onViewAnalysis={handleViewAnalysis}
        />
      )}

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px 0' }}>
        {/* Equipment cards grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 8,
            marginBottom: 16,
          }}
        >
          {EQUIPMENT_LIST.map((e) => {
            const equip = equipmentData[e.id]
            return (
              <EquipmentCard
                key={e.id}
                equip={equip}
                isSelected={selectedEquipment === e.id}
                onClick={() => selectEquipment(e.id)}
              />
            )
          })}
        </div>

        {/* Selected equipment sensor charts */}
        {selectedEquip && (
          <>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--text-muted)',
                letterSpacing: '0.10em',
                marginBottom: 8,
                textTransform: 'uppercase',
              }}
            >
              {selectedEquip.name} — Sensor Trends
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 8,
                paddingBottom: 16,
              }}
            >
              {Object.entries(selectedEquip.sensors).map(([key, sensor]) => (
                <SensorChart
                  key={key}
                  sensorKey={key}
                  sensor={sensor}
                  title={SENSOR_LABELS[key] || key}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
