import React, { useState } from 'react'
import EquipmentCard from './EquipmentCard'
import SensorChart from './SensorChart'
import AlertBanner from './AlertBanner'
import { formatRelativeTime } from '../../utils/formatters'
import { EQUIPMENT_LIST } from '../../services/sensorSimulator'
import { runAnalysis } from '../../services/api'
import useAppStore from '../../store/appStore'

const SENSOR_LABELS = {
  vibration:   'Vibration (mm/s)',
  temperature: 'Bearing Temp (°C)',
  current:     'Motor Current (A)',
  pressure:    'Lube Pressure (bar)',
}

export default function MonitoringPanel({ sensorHook, onSendAlertToChat, chatHook }) {
  const {
    equipmentData,
    alerts,
    selectedEquipment,
    selectEquipment,
    dismissAlert,
    triggerAnomaly,
  } = sensorHook

  const setActivePanel = useAppStore((s) => s.setActivePanel)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const lastUpdated = new Date()
  const topAlert = alerts[0] || null
  const selectedEquip = equipmentData[selectedEquipment]

  const handleViewAnalysis = async (alert) => {
    if (isAnalyzing) return
    
    setIsAnalyzing(true)
    try {
      // Get current sensor data for the equipment
      const equipData = equipmentData[alert.equipmentId]
      const sensorData = {
        vibration: equipData?.sensors?.vibration?.value || 0,
        temperature: equipData?.sensors?.temperature?.value || 0,
        current: equipData?.sensors?.current?.value || 0,
        pressure: equipData?.sensors?.pressure?.value || 0,
      }

      // Call agent analysis API
      const analysisResult = await runAnalysis({
        equipment_id: alert.equipmentId,
        equipment_name: alert.equipmentName,
        alert_description: `${alert.sensorKey} anomaly detected (${alert.value?.toFixed(1)} ${alert.unit || ''})`,
        sensor_data: sensorData,
        anomaly_score: alert.anomalyScore || 0.85,
        risk_level: alert.riskLevel || 'HIGH',
        rul_hours: alert.rulHours || null,
        triggered_by: 'alert',
        alert_id: alert.id,
      })

      // Switch to chat panel and add the analysis as a message
      setActivePanel('chat')
      
      // Add the analysis result as an assistant message in chat
      if (chatHook && chatHook.addAnalysisMessage) {
        chatHook.addAnalysisMessage(analysisResult)
      }

      // Dismiss the alert
      dismissAlert(alert.id)
    } catch (error) {
      console.error('Failed to run analysis:', error)
      // Fallback: send as chat message
      const sensorCfg = EQUIPMENT_LIST.find((e) => e.id === alert.equipmentId)
        ?.sensors?.[alert.sensorKey]
      const threshold = sensorCfg ? (sensorCfg.normal[1]).toFixed(1) : 'N/A'
      const query =
        `ALERT: ${alert.sensorKey} anomaly detected on ${alert.equipmentName}. ` +
        `Reading: ${alert.value?.toFixed(1)} (threshold: ${threshold}). ` +
        `Error running automated analysis: ${error.message}. Please analyze manually.`
      onSendAlertToChat(query)
      dismissAlert(alert.id)
    } finally {
      setIsAnalyzing(false)
    }
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
