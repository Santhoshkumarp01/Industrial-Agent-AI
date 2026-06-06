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
export const getPdfUrl = (docId) => `${BASE}/pdf/${docId}`
