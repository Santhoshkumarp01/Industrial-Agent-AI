import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: BASE })

/**
 * Upload a PDF document with an equipment tag.
 */
export const uploadDocument = async (file, equipmentTag) => {
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('equipment_tag', equipmentTag)
    const res = await client.post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to upload document.')
  }
}

/**
 * Send a chat query and receive an answer with citations.
 */
export const sendChatMessage = async (query, equipmentTag = null, sessionId = null) => {
  try {
    console.log('[API] sendChatMessage called with:', { query: query.substring(0, 50), equipmentTag, sessionId })
    const res = await client.post('/chat', {
      query,
      equipment_tag: equipmentTag || undefined,
      session_id: sessionId || undefined,
    })
    console.log('[API] Response received:', res.data.answer.substring(0, 100))
    return res.data
  } catch (err) {
    console.error('[API] Chat request failed:', err)
    throw new Error(err.response?.data?.detail || 'Failed to get response from AI.')
  }
}

/**
 * Fetch all ingested documents.
 */
export const getDocuments = async () => {
  try {
    const res = await client.get('/documents')
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch documents.')
  }
}

/**
 * Delete a document by ID.
 */
export const deleteDocument = async (docId) => {
  try {
    const res = await client.delete(`/documents/${docId}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to delete document.')
  }
}

/**
 * Resolve a citation reference to page + bbox.
 */
export const getCitation = async (sessionId, refId) => {
  try {
    const res = await client.get(`/citation/${sessionId}/${refId}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to resolve citation.')
  }
}

/**
 * Get the URL to serve a PDF file for the viewer.
 */
export const getPDFUrl = (docId) => `${BASE}/pdf/${docId}`

/**
 * Send a sensor reading to backend ML model for anomaly detection.
 */
export const sendSensorReading = async (reading) => {
  try {
    const res = await client.post('/sensors/reading', reading)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to score sensor reading.')
  }
}

/**
 * Get active alerts from backend.
 */
export const getActiveAlerts = async () => {
  try {
    const res = await client.get('/sensors/alerts')
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch alerts.')
  }
}

/**
 * Acknowledge an alert.
 */
export const acknowledgeAlert = async (alertId) => {
  try {
    const res = await client.post(`/sensors/alerts/${alertId}/acknowledge`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to acknowledge alert.')
  }
}

/**
 * Inject demo anomaly (backend version of Ctrl+Shift+D).
 */
export const injectDemoAnomaly = async (equipmentId = 'RM3') => {
  try {
    const res = await client.post(`/sensors/demo/inject?equipment_id=${equipmentId}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to inject demo anomaly.')
  }
}

/**
 * Get equipment status from backend.
 */
export const getEquipmentStatus = async () => {
  try {
    const res = await client.get('/sensors/status')
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch equipment status.')
  }
}

// ========== AGENT SYSTEM API ==========

/**
 * Run multi-agent analysis on equipment anomaly.
 */
export const runAnalysis = async (analysisRequest) => {
  try {
    const res = await client.post('/agents/analyze', analysisRequest)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to run analysis.')
  }
}

/**
 * Run multi-agent analysis with real-time streaming updates.
 * Returns an async generator that yields progress updates.
 * 
 * Usage:
 *   for await (const update of runAnalysisStreaming(request)) {
 *     console.log(update.message)
 *   }
 */
export async function* runAnalysisStreaming(analysisRequest) {
  const response = await fetch(`${BASE}/agents/analyze-stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(analysisRequest),
  })

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.statusText}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    
    // Split by SSE delimiter
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || '' // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const jsonStr = line.substring(6) // Remove 'data: ' prefix
        try {
          const update = JSON.parse(jsonStr)
          yield update
        } catch (e) {
          console.error('Failed to parse SSE data:', jsonStr, e)
        }
      }
    }
  }
}

/**
 * Submit engineer feedback on an analysis.
 */
export const submitFeedback = async (feedback) => {
  try {
    const res = await client.post('/agents/feedback', feedback)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to submit feedback.')
  }
}

/**
 * Get maintenance logbook entries.
 */
export const getLogbook = async (equipmentId = null, limit = 50) => {
  try {
    const params = {}
    if (equipmentId) params.equipment_id = equipmentId
    if (limit) params.limit = limit
    const res = await client.get('/agents/logbook', { params })
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch logbook.')
  }
}

/**
 * Get a specific logbook entry.
 */
export const getLogbookEntry = async (entryId) => {
  try {
    const res = await client.get(`/agents/logbook/${entryId}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch logbook entry.')
  }
}

/**
 * Get all analysis reports.
 */
export const getReports = async (equipmentId = null, limit = 50) => {
  try {
    const params = {}
    if (equipmentId) params.equipment_id = equipmentId
    if (limit) params.limit = limit
    const res = await client.get('/agents/reports', { params })
    return res.data.reports || []
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch reports.')
  }
}

/**
 * Get a specific report by ID.
 */
export const getReport = async (reportId) => {
  try {
    const res = await client.get(`/agents/reports/${reportId}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch report.')
  }
}

/**
 * Mark a logbook entry as resolved.
 */
export const resolveLogbookEntry = async (entryId, technician = 'Engineer') => {
  try {
    const res = await client.post(`/agents/logbook/${entryId}/resolve`, null, {
      params: { technician }
    })
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to resolve logbook entry.')
  }
}

/**
 * Get feedback accuracy statistics.
 */
export const getFeedbackStats = async () => {
  try {
    const res = await client.get('/agents/feedback/stats')
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch feedback stats.')
  }
}

// ========== MACHINE ANALYSIS API ==========

/**
 * Get latest dynamic machine logs for a specific equipment tag.
 */
export const getMachineLogs = async (machineTag, count = 10) => {
  try {
    const res = await client.get(`/machine-analysis/logs/${machineTag}`, {
      params: { count },
    })
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch machine logs.')
  }
}

/**
 * Get machine summary (latest reading + thresholds).
 */
export const getMachineSummary = async (machineTag) => {
  try {
    const res = await client.get(`/machine-analysis/summary/${machineTag}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to fetch machine summary.')
  }
}

/**
 * Run full RAG analysis for a machine:
 * fetches logs → retrieves PDF chunks → generates LLM answer.
 * Answer is NEVER predefined — dynamically generated from logs + document.
 */
export const runMachineAnalysis = async (machineTag, options = {}) => {
  try {
    const res = await client.post(`/machine-analysis/analyze/${machineTag}`, {
      include_logs: options.includeLogs || 10,
      inject_anomaly: options.injectAnomaly || false,
    })
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to run machine analysis.')
  }
}

/**
 * Inject a demo anomaly for a machine (spikes a random sensor to critical).
 */
export const injectMachineAnomaly = async (machineTag) => {
  try {
    const res = await client.post(`/machine-analysis/inject-anomaly/${machineTag}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to inject anomaly.')
  }
}

/**
 * Reset machine sensors to normal operating baseline.
 */
export const resetMachine = async (machineTag) => {
  try {
    const res = await client.post(`/machine-analysis/reset/${machineTag}`)
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to reset machine.')
  }
}

/**
 * List all configured machines with their document mappings.
 */
export const listMachines = async () => {
  try {
    const res = await client.get('/machine-analysis/machines')
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to list machines.')
  }
}

/**
 * Submit engineer feedback on a chat assistant answer.
 */
export const submitChatFeedback = async (sessionId, messageId, query, answer, verdict) => {
  try {
    const form = new FormData()
    form.append('session_id', sessionId)
    form.append('message_id', messageId)
    form.append('query', query)
    form.append('answer', answer)
    form.append('verdict', verdict) // "positive" or "negative"
    
    const res = await client.post('/chat/feedback', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  } catch (err) {
    throw new Error(err.response?.data?.detail || 'Failed to submit chat feedback.')
  }
}
