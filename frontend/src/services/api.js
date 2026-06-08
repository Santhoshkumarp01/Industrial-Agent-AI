import axios from 'axios'

const BASE = 'http://localhost:8000'

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
    const res = await client.post('/chat', {
      query,
      equipment_tag: equipmentTag || undefined,
      session_id: sessionId || undefined,
    })
    return res.data
  } catch (err) {
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
