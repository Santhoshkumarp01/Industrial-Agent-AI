import React, { useState, useEffect, useRef } from 'react'
import EquipmentCard from './EquipmentCard'
import SensorChart from './SensorChart'
import AlertBanner from './AlertBanner'
import MonitorChatPanel from './MonitorChatPanel'
import AgentStreamingStatus from './AgentStreamingStatus'
import MonitorOnboardingTour from '../onboarding/MonitorOnboardingTour'
import { formatRelativeTime } from '../../utils/formatters'
import { EQUIPMENT_LIST } from '../../services/sensorSimulator'
import { runMachineAnalysis, injectMachineAnomaly, getMachineLogs, runAnalysisStreaming } from '../../services/api'
import useAppStore from '../../store/appStore'
import { trackEvent, trackAnalysisRun } from '../../utils/analytics'

const SENSOR_LABELS = {
  vibration:   'Vibration (mm/s)',
  temperature: 'Bearing Temp (°C)',
  current:     'Motor Current (A)',
  pressure:    'Lube Pressure (bar)',
}

export default function MonitoringPanel({ sensorHook, chatHook, documentsHook }) {
  const {
    equipmentData,
    alerts,
    selectedEquipment,
    selectEquipment,
    dismissAlert,
  } = sensorHook

  const setActiveCitation = useAppStore((s) => s.setActiveCitation)
  const activePanel = useAppStore((s) => s.activePanel)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [backendMachineLogs, setBackendMachineLogs] = useState({})
  const [streamingUpdates, setStreamingUpdates] = useState([]) // Agent progress updates
  const analyzingIdRef = useRef(null) // tracks the "analyzing..." message id so we can replace it

  const lastUpdated = new Date()
  const topAlert = alerts[0] || null
  const selectedEquip = equipmentData[selectedEquipment]

  // ── Fetch backend machine logs every 5s ──────────────────────────────────
  useEffect(() => {
    const fetchAllMachineLogs = async () => {
      try {
        const results = await Promise.all(
          EQUIPMENT_LIST.map(async (equip) => {
            const data = await getMachineLogs(equip.id, 5)
            return { machineTag: equip.id, data }
          })
        )
        const logsMap = {}
        results.forEach(({ machineTag, data }) => {
          logsMap[machineTag] = data
        })
        setBackendMachineLogs(logsMap)
      } catch (error) {
        console.error('Failed to fetch backend machine logs:', error)
      }
    }
    fetchAllMachineLogs()
    const intervalId = setInterval(fetchAllMachineLogs, 5000)
    return () => clearInterval(intervalId)
  }, [])

  // ── Open the PDF for the machine's mapped manual ─────────────────────────
  const openMachineManual = (mappedDocName) => {
    if (!mappedDocName) return
    const docs = documentsHook?.documents || []
    // doc_name in Qdrant is the original filename (e.g. "Steel Plant - Rolling Mill...")
    const doc = docs.find(
      (d) => d.doc_name === mappedDocName || d.doc_name?.includes(mappedDocName)
    )
    if (doc) {
      // Open PDF viewer at page 1 with the doc_id
      setActiveCitation({
        doc_id:      doc.doc_id,
        doc_name:    doc.doc_name,
        page_number: 1,
        bbox:        null,
        ref:         '📄 MANUAL',
      })
    }
  }

  // ── Run analysis with streaming progress updates ─────────────────────────
  const runAnalysis = async (machineTag, machineName) => {
    if (isAnalyzing) return
    setIsAnalyzing(true)
    setStreamingUpdates([]) // Clear previous updates

    // Show streaming status component in chat
    const streamingId = chatHook?.addAnalyzingMessage(
      `Running 3-agent analysis for ${machineName}`
    )
    analyzingIdRef.current = streamingId

    try {
      // Get the latest backend logs to build the analysis request
      const logsData = await getMachineLogs(machineTag, 10)
      const latestLog = logsData.logs?.[logsData.logs.length - 1]

      if (!latestLog) {
        throw new Error('No sensor data available for analysis')
      }

      const analysisRequest = {
        equipment_id: machineTag,
        equipment_name: machineName,
        alert_description: latestLog.event_summary || 'Anomaly detected',
        sensor_data: {
          vibration_mm_s: latestLog.vibration_velocity_mm_s,
          bearing_temp_c: latestLog.bearing_temp_drive_end_c,
          motor_current_a: latestLog.stator_phase_current_a,
          lube_pressure_bar: latestLog.bearing_lube_oil_pressure_bar,
          rpm: latestLog.shaft_speed_rpm
        },
        anomaly_score: latestLog.severity === 'CRITICAL' ? 0.9 : latestLog.severity === 'WARNING' ? 0.7 : 0.3,
        risk_level: latestLog.severity || 'MEDIUM',
        rul_hours: null,
        triggered_by: 'live_monitor',
        alert_id: null,
        session_id: null,
        severity: latestLog.severity || 'WARNING',  // Pass severity for RUL calculation
        fault_code: latestLog.fault_code !== '—' ? latestLog.fault_code : null  // Pass fault code
      }

      // Stream the analysis with real-time updates
      const updates = []
      for await (const update of runAnalysisStreaming(analysisRequest)) {
        updates.push(update)
        setStreamingUpdates([...updates])

        // If complete, show final result
        if (update.type === 'complete') {
          chatHook?.replaceAnalyzingMessage(streamingId, {
            ...update.data,
            logbook_entry_id: update.data.logbook_entry_id,
            streaming_updates: updates
          })
          break
        }
      }

    } catch (err) {
      console.error('Analysis failed:', err)
      chatHook?.replaceAnalyzingWithError(streamingId, `Analysis failed for ${machineName}: ${err.message}`)
    } finally {
      setIsAnalyzing(false)
      setStreamingUpdates([])
    }
  }

  // ── Equipment card clicked → show quick-action prompt in monitor chat ──
  const handleCardClick = (machineTag, machineName, latestLog) => {
    selectEquipment(machineTag)
    // Open the machine's mapped PDF manual
    openMachineManual(latestLog?.mapped_document)

    const severity = latestLog?.severity || 'NORMAL'
    const faultCode = latestLog?.fault_code && latestLog.fault_code !== '—' ? ` (${latestLog.fault_code})` : ''
    const statusLine = severity === 'NORMAL'
      ? `✅ All sensors within normal range.`
      : severity === 'WARNING'
        ? `⚠️ WARNING detected${faultCode} — sensor anomaly present.`
        : `🚨 CRITICAL fault${faultCode} — immediate attention required.`

    // Show a contextual prompt card in monitor chat
    chatHook?.addEquipmentPrompt({
      machineTag,
      machineName,
      severity,
      statusLine,
      latestLog,
    })
  }
  const handleViewAnalysis = async (alert) => {
    if (isAnalyzing) return
    const machineTag = alert.equipmentId
    const machineName = alert.equipmentName

    // Inject backend anomaly first so logs show the issue
    try {
      await injectMachineAnomaly(machineTag)
      await new Promise((res) => setTimeout(res, 400))
    } catch (_) { /* ignore */ }

    dismissAlert(alert.id)
    await runAnalysis(machineTag, machineName)
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden', minWidth: 0 }}>

      {/* ── Left: equipment dashboard ──────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>

        {/* Panel header */}
        <div style={{
          height: 44,
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 14 }}>📡</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)', letterSpacing: '0.08em' }}>
              LIVE MONITOR INTELLIGENCE
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              data-tour="demo-anomaly"
              onClick={async () => {
                const machineTag = 'general-industrial-motor'
                const machineName = 'General Industrial Motor'
                
                // Track demo anomaly click
                trackEvent('demo_anomaly_clicked', {
                  equipment: machineTag,
                  panel: 'monitor',
                })
                
                // Inject anomaly
                try {
                  await injectMachineAnomaly(machineTag)
                  selectEquipment(machineTag)
                  
                  // Wait and run analysis
                  setTimeout(async () => {
                    await runAnalysis(machineTag, machineName)
                  }, 2000)
                } catch (err) {
                  console.error('Demo anomaly failed:', err)
                }
              }}
              disabled={isAnalyzing}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                padding: '5px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--status-critical)',
                background: isAnalyzing ? 'var(--bg-surface)' : 'rgba(232,93,93,0.08)',
                color: isAnalyzing ? 'var(--text-muted)' : 'var(--status-critical)',
                cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                letterSpacing: '0.04em',
                opacity: isAnalyzing ? 0.5 : 1,
              }}
              onMouseEnter={(e) => {
                if (!isAnalyzing) e.currentTarget.style.background = 'rgba(232,93,93,0.15)'
              }}
              onMouseLeave={(e) => {
                if (!isAnalyzing) e.currentTarget.style.background = 'rgba(232,93,93,0.08)'
              }}
              title="Inject demo vibration anomaly on Rolling Mill for testing"
            >
              DEMO ANOMALY
            </button>

            {/* Tour button - Live Monitor guide */}
            <button
              onClick={() => {
                localStorage.setItem('activePanel', 'monitor')
                localStorage.removeItem('industrial_agent_monitor_onboarding_complete')
                window.location.reload()
              }}
              title="Start Monitor Intelligence guide"
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                padding: '5px 10px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--accent-amber)',
                background: 'rgba(245, 166, 35, 0.1)',
                color: 'var(--accent-amber)',
                cursor: 'pointer',
                letterSpacing: '0.05em',
                transition: 'all 0.3s ease',
                boxShadow: '0 0 15px rgba(245, 166, 35, 0.3), 0 0 30px rgba(245, 166, 35, 0.15)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(245, 166, 35, 0.18)'
                e.currentTarget.style.boxShadow = '0 0 25px rgba(245, 166, 35, 0.5), 0 0 50px rgba(245, 166, 35, 0.3)'
                e.currentTarget.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(245, 166, 35, 0.1)'
                e.currentTarget.style.boxShadow = '0 0 15px rgba(245, 166, 35, 0.3), 0 0 30px rgba(245, 166, 35, 0.15)'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              TOUR
            </button>

            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
              UPDATED {formatRelativeTime(lastUpdated).toUpperCase()}
            </span>
          </div>
        </div>

        {/* Alert banner */}
        {topAlert && (
          <AlertBanner
            alert={topAlert}
            onDismiss={dismissAlert}
            onViewAnalysis={handleViewAnalysis}
          />
        )}

        {/* Scrollable content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px 0' }}>

          {/* Show streaming agent status when analysis is running */}
          {isAnalyzing && streamingUpdates.length > 0 && (
            <AgentStreamingStatus updates={streamingUpdates} />
          )}

          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em', marginBottom: 8, textTransform: 'uppercase' }}>
            Equipment Status — {EQUIPMENT_LIST.length} machines monitored
          </div>

          {/* Equipment cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, marginBottom: 16 }}>
            {EQUIPMENT_LIST.map((e) => {
              const equip = equipmentData[e.id]
              const machineLogData = backendMachineLogs[e.id]
              const latestBackendLog = machineLogData?.logs?.[machineLogData.logs.length - 1]

              return (
                <EquipmentCard
                  key={e.id}
                  equip={equip}
                  backendLog={latestBackendLog}
                  isSelected={selectedEquipment === e.id}
                  isAnalyzing={isAnalyzing && selectedEquipment === e.id}
                  onClick={() => {
                    handleCardClick(e.id, equip?.name || e.id, latestBackendLog)
                  }}
                />
              )
            })}
          </div>

          {/* Sensor charts for selected machine */}
          {selectedEquip && (
            <>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em', marginBottom: 8, textTransform: 'uppercase' }}>
                {selectedEquip.name} — Live Sensor Trends
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, paddingBottom: 16 }}>
                {Object.entries(selectedEquip.sensors).map(([key, sensor]) => (
                  <SensorChart key={key} sensorKey={key} sensor={sensor} title={SENSOR_LABELS[key] || key} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Right: Monitor AI chat (always visible, separate history) ──── */}
      <div
        data-tour="monitor-chat"
        style={{
          width: 400,
          flexShrink: 0,
          borderLeft: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <MonitorChatPanel
          chatHook={chatHook}
          isAnalyzing={isAnalyzing}
          onRunAnalysis={runAnalysis}
        />
      </div>

      {/* Onboarding Tour - only for Monitor panel */}
      {activePanel === 'monitor' && <MonitorOnboardingTour />}
    </div>
  )
}
