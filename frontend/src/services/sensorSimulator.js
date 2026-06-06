const EQUIPMENT = [
  {
    id: 'rm1',
    name: 'Rolling Mill #1',
    tag: 'Rolling Mill',
    sensors: {
      vibration:    { normal: [1.5, 3.0], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [65, 78],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [38, 46],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [4.2, 5.1], unit: 'bar',  label: 'Lube Pressure' },
    },
  },
  {
    id: 'rm3',
    name: 'Rolling Mill #3',
    tag: 'Rolling Mill',
    sensors: {
      vibration:    { normal: [1.5, 3.0], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [65, 78],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [38, 46],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [4.2, 5.1], unit: 'bar',  label: 'Lube Pressure' },
    },
  },
  {
    id: 'bf1',
    name: 'BF Blower #1',
    tag: 'Blast Furnace',
    sensors: {
      vibration:    { normal: [0.8, 2.0], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [55, 70],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [52, 62],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [6.1, 7.4], unit: 'bar',  label: 'Lube Pressure' },
    },
  },
  {
    id: 'comp_a',
    name: 'Compressor A',
    tag: 'Compressor',
    sensors: {
      vibration:    { normal: [1.2, 2.8], unit: 'mm/s', label: 'Vibration' },
      temperature:  { normal: [72, 88],   unit: '°C',   label: 'Bearing Temp' },
      current:      { normal: [28, 36],   unit: 'A',    label: 'Motor Current' },
      pressure:     { normal: [8.5, 10.2],unit: 'bar',  label: 'Lube Pressure' },
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
