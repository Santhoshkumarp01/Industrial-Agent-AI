import { useState, useEffect, useCallback, useRef } from 'react'
import { createSimulator, injectAnomaly, EQUIPMENT_LIST } from '../services/sensorSimulator'
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
    const handleReading = (equipId, sensorKey, value, timestamp, isAnomaly) => {
      setEquipmentData((prev) => {
        const equip = prev[equipId]
        if (!equip) return prev

        const sensor = equip.sensors[sensorKey]
        if (!sensor) return prev

        const newReading = { value, timestamp, isAnomaly }
        const updatedReadings = [...sensor.readings, newReading].slice(-MAX_READINGS)

        // Derive equipment status
        const hasCritical = Object.values({
          ...equip.sensors,
          [sensorKey]: { ...sensor, readings: updatedReadings, isAnomaly },
        }).some((s) => s.readings?.slice(-1)[0]?.isAnomaly)

        return {
          ...prev,
          [equipId]: {
            ...equip,
            status: hasCritical ? 'critical' : 'ok',
            riskLevel: hasCritical ? 'CRITICAL' : 'NORMAL',
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
  }, []) // eslint-disable-line

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
