import React, { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  ReferenceDot,
  CartesianGrid,
} from 'recharts'
import { formatTimeOnly } from '../../utils/formatters'

export default function SensorChart({ sensorKey, sensor, title }) {
  if (!sensor) return null

  const readings = sensor.readings || []
  const hasAnomaly = readings.some((r) => r.isAnomaly)
  const lineColor = hasAnomaly ? 'var(--status-critical)' : 'var(--accent-blue)'

  const data = useMemo(
    () =>
      readings.map((r, i) => ({
        index: i,
        value: r.value,
        time: formatTimeOnly(r.timestamp),
        isAnomaly: r.isAnomaly,
      })),
    [readings]
  )

  const anomalyPoints = data.filter((d) => d.isAnomaly)

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 12px',
        position: 'relative',
      }}
    >
      {/* Chart title */}
      <div style={{ marginBottom: 8 }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--accent-amber)',
            letterSpacing: '0.06em',
          }}
        >
          {title || sensorKey?.toUpperCase()}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', marginLeft: 8 }}>
          {sensor.unit}
        </span>
        {sensor.latestValue !== null && (
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
              color: hasAnomaly ? 'var(--status-critical)' : 'var(--text-primary)',
              float: 'right',
              animation: 'countUp 0.3s ease',
            }}
          >
            {sensor.latestValue?.toFixed(1)}
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={80}>
        <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 0 }}>
          <CartesianGrid
            strokeDasharray="0"
            horizontal
            vertical={false}
            stroke="#1A1F2E"
          />
          <XAxis
            dataKey="index"
            tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--text-muted)' }}
            tickLine={false}
            axisLine={false}
            interval={14}
            tickFormatter={(i) => data[i]?.time?.slice(0, 5) || ''}
          />
          <YAxis
            tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--text-muted)' }}
            tickLine={false}
            axisLine={false}
            width={28}
            tickFormatter={(v) => v.toFixed(0)}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
          {anomalyPoints.map((pt) => (
            <ReferenceDot
              key={pt.index}
              x={pt.index}
              y={pt.value}
              r={3}
              fill="var(--status-critical)"
              stroke="none"
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
