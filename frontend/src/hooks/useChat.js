import { useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { sendChatMessage } from '../services/api'

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content:
    'Industrial Agent AI - Intelligent Maintenance Assistant\n\n' +
    'Powered by fine-tuned Phi-3.5 Mini specialized for industrial equipment\n\n' +
    'Key Features:\n' +
    '• Expert answers with exact manual citations\n' +
    '• RAG pipeline with 4 pre-loaded equipment manuals\n' +
    '• Document-grounded responses for accuracy\n\n' +
    'Model Card: https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora\n\n' +
    'Upload a document or ask about existing equipment to get started.',
  citations: [],
  timestamp: new Date(),
}

const MONITOR_WELCOME_MESSAGE = {
  id: 'monitor-welcome',
  role: 'assistant',
  content: 'Live Monitor Intelligence - Real-Time Equipment Monitoring\n\n' +
    '3-Agent Diagnostic System for intelligent fault detection\n\n' +
    'Agent Pipeline:\n' +
    '1. Root Cause Analysis - Identifies failure patterns\n' +
    '2. Risk Assessment - Predicts remaining useful life (RUL)\n' +
    '3. Maintenance Planning - Generates action plans with spare parts\n\n' +
    'Quick Start: Click "DEMO ANOMALY" to see AI analysis in action\n\n' +
    'Real-time sensor data with automated fault detection and diagnostics.',
  citations: [],
  timestamp: new Date(),
}

export const useChat = ({ isMonitor = false } = {}) => {
  const [messages, setMessages] = useState([isMonitor ? MONITOR_WELCOME_MESSAGE : WELCOME_MESSAGE])
  const [sessionId] = useState(() => uuidv4())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const sendMessage = useCallback(
    async (query, equipmentTag = null) => {
      if (!query.trim()) return

      const userMsg = {
        id: uuidv4(),
        role: 'user',
        content: query,
        citations: [],
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)
      setError(null)

      try {
        const data = await sendChatMessage(query, equipmentTag, sessionId)

        const assistantMsg = {
          id: uuidv4(),
          role: 'assistant',
          content: data.answer,
          citations: data.citations || [],
          retrievedChunks: data.retrieved_chunks || [],
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMsg])
      } catch (err) {
        setError(err.message)
        const errMsg = {
          id: uuidv4(),
          role: 'assistant',
          content: `Error: ${err.message}`,
          citations: [],
          timestamp: new Date(),
          isError: true,
        }
        setMessages((prev) => [...prev, errMsg])
      } finally {
        setIsLoading(false)
      }
    },
    [sessionId]
  )

  const clearChat = useCallback(() => {
    setMessages([isMonitor ? MONITOR_WELCOME_MESSAGE : WELCOME_MESSAGE])
    setError(null)
  }, [isMonitor])

  const addAnalysisMessage = useCallback((analysisResult) => {
    // Detect machine analysis format vs old agent format
    const isMachineAnalysis = !!analysisResult.machine_tag

    const analysisMsg = {
      id: uuidv4(),
      role: 'assistant',
      content: isMachineAnalysis ? analysisResult.analysis?.answer || '' : '',
      citations: isMachineAnalysis ? (analysisResult.analysis?.citations || []) : [],
      timestamp: new Date(),
      analysisData: analysisResult,
      // Old agent format uses logbook_entry_id; machine analysis doesn't
      logbookEntryId: analysisResult.logbook_entry_id || null,
      isMachineAnalysis,
    }
    setMessages((prev) => [...prev, analysisMsg])
  }, [])

  const addEquipmentPrompt = useCallback(({ machineTag, machineName, severity, statusLine, latestLog }) => {
    const id = uuidv4()
    const promptMsg = {
      id,
      role: 'assistant',
      content: '',
      citations: [],
      timestamp: new Date(),
      isEquipmentPrompt: true,
      equipmentPrompt: { machineTag, machineName, severity, statusLine, latestLog },
    }
    // Replace any existing equipment prompt — don't stack multiple cards
    setMessages((prev) => {
      const withoutOldPrompts = prev.filter((m) => !m.isEquipmentPrompt)
      return [...withoutOldPrompts, promptMsg]
    })
    return id
  }, [])

  const addAnalyzingMessage = useCallback((text) => {
    const id = uuidv4()
    const analyzingMsg = {
      id,
      role: 'assistant',
      content: text,
      citations: [],
      timestamp: new Date(),
      isAnalyzing: true,
    }
    setMessages((prev) => [...prev, analyzingMsg])
    return id  // caller can use this to replace the message later
  }, [])

  // Replace an "analyzing..." placeholder with the real analysis result
  const replaceAnalyzingMessage = useCallback((analyzingId, analysisResult) => {
    const isMachineAnalysis = !!analysisResult.machine_tag
    const finalMsg = {
      id: analyzingId || uuidv4(),
      role: 'assistant',
      content: isMachineAnalysis ? analysisResult.analysis?.answer || '' : '',
      citations: isMachineAnalysis ? (analysisResult.analysis?.citations || []) : [],
      timestamp: new Date(),
      analysisData: analysisResult,
      logbookEntryId: analysisResult.logbook_entry_id || null,
      isMachineAnalysis,
      isAnalyzing: false,
    }
    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === analyzingId)
      if (idx === -1) return [...prev, finalMsg]
      const next = [...prev]
      next[idx] = finalMsg
      return next
    })
  }, [])

  // Replace an "analyzing..." placeholder with an error message
  const replaceAnalyzingWithError = useCallback((analyzingId, errorText) => {
    const errMsg = {
      id: analyzingId || uuidv4(),
      role: 'assistant',
      content: errorText,
      citations: [],
      timestamp: new Date(),
      isError: true,
      isAnalyzing: false,
    }
    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === analyzingId)
      if (idx === -1) return [...prev, errMsg]
      const next = [...prev]
      next[idx] = errMsg
      return next
    })
  }, [])

  return { messages, sessionId, isLoading, error, sendMessage, clearChat, addAnalysisMessage, addAnalyzingMessage, replaceAnalyzingMessage, replaceAnalyzingWithError, addEquipmentPrompt }
}
