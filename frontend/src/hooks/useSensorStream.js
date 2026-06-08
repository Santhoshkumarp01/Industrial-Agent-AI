import { useState, useEffect, useCallback, useRef } from 'react'
import { createSimulator, injectAnomaly, EQUIPMENT_LIST } from '../services/sensorSimulator'
import { sendSensorReading, getActiveAlerts } from '../services/api'
import useAppStore from '../store/appStore'

const MAX_READINGS = 60

// Build initial state structure
const buildInitialState = () => {
  const state = {}
  for (const equip of EQUIPMENT_LIST) {
    state[equip.id] = {
      id: equip.id,
      name: equip.name,
      tag: equip.tag,
      status: 'ok',
      riskLevel: 'NORMAL',
      sensors: {},
    }
    for (const [key, cfg] of Object.entries(equip.sensors)) {
      state[equip.id].sensors[key] = {
        label: cfg.label,
        unit: cfg.unit,
        normal: cfg.normal,
        readings: [],
        latestValue: null,
        isAnomaly: false,
      }
    }
  }
  return state
}

export const useSensorStream = (onAlertDetected) => {
  const [equipmentData, setEquipmentData] = useState(buildInitialState)
  const [alerts, setAlerts] = useState([])
  const [selectedEquipment, setSelectedEquipment] = useState('rm3')
  const simulatorRef = useRef(null)
  const incrementAlerts = useAppStore((s) => s.incrementAlerts)

  useEffect(() => {
    const handleReading = async (equipId, sensorKey, value, timestamp, isAnomalyClient) => {
      // Get current sensor values for this equipment
      const currentEquip = equipmentData[equipId]
      if (!currentEquip) return

      // Build sensor reading object for backend
      const sensorReading = {
        equipment_id: equipId.toUpperCase(),
        vibration: sensorKey === 'vibration' ? value : (currentEquip.sensors.vibration?.latestValue || 2.0),
        temperature: sensorKey === 'temperature' ? value : (currentEquip.sensors.temperature?.latestValue || 70.0),
        current: sensorKey === 'current' ? value : (currentEquip.sensors.current?.latestValue || 40.0),
        pressure: sensorKey === 'pressure' ? value : (currentEquip.sensors.pressure?.latestValue || 5.0),
        timestamp: timestamp.toISOString()
      }

      // Send to backend ML model for prediction
      let prediction = null
      let isAnomaly = isAnomalyClient // fallback to client-side detection
      let riskLevel = 'NORMAL'

      try {
        prediction = await sendSensorReading(sensorReading)
        isAnomaly = prediction.is_anomaly
        riskLevel = prediction.risk_level
      } catch (err) {
        console.warn('Backend ML unavailable, using client-side threshold detection:', err.message)
        // Fallback to client-side threshold
        isAnomaly = isAnomalyClient
        riskLevel = isAnomalyClient ? 'CRITICAL' : 'NORMAL'
      }

      setEquipmentData((prev) => {
        const equip = prev[equipId]
        if (!equip) return prev

        const sensor = equip.sensors[sensorKey]
        if (!sensor) return prev

        const newReading = { value, timestamp, isAnomaly }
        const updatedReadings = [...sensor.readings, newReading].slice(-MAX_READINGS)

        // Derive equipment status from prediction
        const hasCritical = isAnomaly || riskLevel === 'CRITICAL' || riskLevel === 'HIGH'

        return {
          ...prev,
          [equipId]: {
            ...equip,
            status: hasCritical ? 'critical' : 'ok',
            riskLevel: riskLevel,
            sensors: {
              ...equip.sensors,
              [sensorKey]: {
                ...sensor,
                readings: updatedReadings,
                latestValue: value,
                isAnomaly,
              },
            },
          },
        }
      })
    }

    const handleAlert = (equipId, sensorKey, value, equipName) => {
      const alertId = `${equipId}_${sensorKey}_${Date.now()}`
      const alert = {
        id: alertId,
        equipmentId: equipId,
        equipmentName: equipName,
        sensorKey,
        value,
        timestamp: new Date(),
      }
      setAlerts((prev) => {
        // Deduplicate: only add if no alert for same equip+sensor in last 10s
        const recent = prev.find(
          (a) =>
            a.equipmentId === equipId &&
            a.sensorKey === sensorKey &&
            Date.now() - new Date(a.timestamp).getTime() < 10000
        )
        if (recent) return prev
        return [alert, ...prev].slice(0, 5)
      })
      incrementAlerts()
      if (onAlertDetected) onAlertDetected(alert)
    }

    simulatorRef.current = createSimulator(handleReading, handleAlert)

    return () => {
      simulatorRef.current?.stop()
    }
  }, [equipmentData]) // Re-run when equipment data changes to get latest sensor values

  // Poll backend alerts every 5 seconds
  useEffect(() => {
    const pollAlerts = async () => {
      try {
        const backendAlerts = await getActiveAlerts()
        // Merge backend alerts with local alerts
        setAlerts((prev) => {
          const backendAlertIds = new Set(backendAlerts.map(a => a.alert_id))
          const localAlertsFiltered = prev.filter(a => !a.backend)
          
          const formattedBackendAlerts = backendAlerts.map(a => ({
            id: a.alert_id,
            equipmentId: a.equipment_id.toLowerCase(),
            equipmentName: a.equipment_name,
            sensorKey: a.sensor_key,
            value: a.sensor_value,
            timestamp: new Date(a.timestamp),
            backend: true,
            rulHours: a.rul_hours,
            riskLevel: a.risk_level,
            anomalyScore: a.anomaly_score
          }))

          return [...formattedBackendAlerts, ...localAlertsFiltered].slice(0, 10)
        })
      } catch (err) {
        console.warn('Failed to fetch backend alerts:', err.message)
      }
    }

    pollAlerts()
    const interval = setInterval(pollAlerts, 5000)
    return () => clearInterval(interval)
  }, [])

  const selectEquipment = useCallback((id) => setSelectedEquipment(id), [])

  const dismissAlert = useCallback((id) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }, [])

  const triggerAnomaly = useCallback((equipId, sensorKey) => {
    injectAnomaly(equipId, sensorKey)
  }, [])

  return {
    equipmentData,
    alerts,
    selectedEquipment,
    selectEquipment,
    dismissAlert,
    triggerAnomaly,
  }
}
