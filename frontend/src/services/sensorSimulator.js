const EQUIPMENT = [
  {
    id: 'general-industrial-motor',
    backendId: 'general-industrial-motor',
    name: 'General Industrial Motor',
    tag: 'general-industrial-motor',
    sensors: {
      vibration:    { normal: [1.0, 2.5], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [60, 75],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [20, 30],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [3.8, 4.8], unit: 'bar',  label: 'Lube Pressure' },
    },
  },
  {
    id: 'ac-drive-motor',
    backendId: 'ac-drive-motor',
    name: 'AC Drive Motor',
    tag: 'ac-drive-motor',
    sensors: {
      vibration:    { normal: [1.5, 3.0], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [65, 78],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [38, 46],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [4.2, 5.1], unit: 'bar',  label: 'Lube Pressure' },
    },
  },
  {
    id: 'synchronous-motor',
    backendId: 'synchronous-motor',
    name: 'Synchronous Motor',
    tag: 'synchronous-motor',
    sensors: {
      vibration:    { normal: [1.2, 2.8], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [70, 85],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [25, 35],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [4.0, 5.0], unit: 'bar',  label: 'Lube Pressure' },
    },
  },
  {
    id: 'heavy-duty-industrial-motor',
    backendId: 'heavy-duty-industrial-motor',
    name: 'Heavy-Duty Industrial Motor',
    tag: 'heavy-duty-industrial-motor',
    sensors: {
      vibration:    { normal: [0.8, 2.0], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [55, 70],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [52, 62],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [6.1, 7.4], unit: 'bar',  label: 'Lube Pressure' },
    },
  },
]

export const EQUIPMENT_LIST = EQUIPMENT

// Track anomaly injection counters: { [equipId_sensorKey]: remainingReadings }
const anomalyCounters = {}

const randBetween = (min, max) => min + Math.random() * (max - min)

const addNoise = (value, pct = 0.05) => {
  const noise = (Math.random() * 2 - 1) * pct * value
  return value + noise
}

/**
 * Inject an anomaly into a specific equipment sensor for 8 readings.
 */
export const injectAnomaly = (equipmentId, sensorKey) => {
  const key = `${equipmentId}_${sensorKey}`
  anomalyCounters[key] = 8
}

/**
 * Create and start the sensor simulator.
 *
 * @param {Function} onReading - (equipmentId, sensorKey, value, timestamp, isAnomaly) => void
 * @param {Function} onAlert   - (equipmentId, sensorKey, value, equipmentName) => void
 * @returns {{ stop: Function, injectAnomaly: Function }}
 */
export const createSimulator = (onReading, onAlert) => {
  const intervalId = setInterval(() => {
    const now = new Date()

    for (const equip of EQUIPMENT) {
      for (const [sensorKey, sensorCfg] of Object.entries(equip.sensors)) {
        const anomalyKey = `${equip.id}_${sensorKey}`
        let value
        let isAnomaly = false

        if (anomalyCounters[anomalyKey] > 0) {
          // Spike to 2.5–3× normal max
          const spikeMultiplier = 2.5 + Math.random() * 0.5
          value = sensorCfg.normal[1] * spikeMultiplier
          isAnomaly = true
          anomalyCounters[anomalyKey] -= 1
        } else {
          value = addNoise(randBetween(sensorCfg.normal[0], sensorCfg.normal[1]))
          // Frontend anomaly detection: reading > 2× normal max
          if (value > sensorCfg.normal[1] * 2) {
            isAnomaly = true
          }
        }

        value = Math.round(value * 10) / 10

        onReading(equip.id, sensorKey, value, now, isAnomaly)

        if (isAnomaly) {
          onAlert(equip.id, sensorKey, value, equip.name)
        }
      }
    }
  }, 3000)

  return {
    stop: () => clearInterval(intervalId),
    injectAnomaly,
  }
}
