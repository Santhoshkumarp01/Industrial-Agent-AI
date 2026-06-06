/**
 * Format a Date into HH:MM:SS
 */
export const formatTimestamp = (date) => {
  const d = date instanceof Date ? date : new Date(date)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

/**
 * Format a sensor value with its unit
 * e.g. formatSensorValue(8.73, 'mm/s') → '8.7 mm/s'
 */
export const formatSensorValue = (value, unit) => {
  if (value === null || value === undefined) return `-- ${unit}`
  return `${Number(value).toFixed(1)} ${unit}`
}

/**
 * Return a human-readable relative time string
 * e.g. '2 min ago', 'just now'
 */
export const formatRelativeTime = (date) => {
  const d = date instanceof Date ? date : new Date(date)
  const diffMs = Date.now() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 5) return 'just now'
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin} min ago`
  const diffHr = Math.floor(diffMin / 60)
  return `${diffHr}h ago`
}

/**
 * Return the CSS variable string for a given risk level
 */
export const getRiskColor = (level) => {
  switch ((level || '').toUpperCase()) {
    case 'CRITICAL': return 'var(--status-critical)'
    case 'HIGH':     return 'var(--accent-amber)'
    case 'MEDIUM':   return 'var(--accent-blue)'
    case 'LOW':      return 'var(--status-ok)'
    default:         return 'var(--text-secondary)'
  }
}

/**
 * Derive equipment risk level from its sensor readings
 */
export const deriveRiskLevel = (sensors) => {
  if (!sensors) return 'NORMAL'
  for (const key of Object.keys(sensors)) {
    const readings = sensors[key]?.readings || []
    if (readings.length === 0) continue
    const latest = readings[readings.length - 1]
    if (latest?.isAnomaly) return 'CRITICAL'
  }
  return 'NORMAL'
}
