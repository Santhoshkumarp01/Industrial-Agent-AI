import { useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { sendChatMessage } from '../services/api'

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content:
    'System online. Upload a maintenance document and ask your first question. ' +
    'I will answer with exact citations from your uploaded manuals.',
  citations: [],
  timestamp: new Date(),
}

export const useChat = () => {
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
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
    setMessages([WELCOME_MESSAGE])
    setError(null)
  }, [])

  const addAnalysisMessage = useCallback((analysisResult) => {
    const analysisMsg = {
      id: uuidv4(),
      role: 'assistant',
      content: '', // Content will be rendered by AgentAnalysisContent component
      citations: [],
      timestamp: new Date(),
      analysisData: analysisResult,
      logbookEntryId: analysisResult.logbook_entry_id,
    }
    setMessages((prev) => [...prev, analysisMsg])
  }, [])

  return { messages, sessionId, isLoading, error, sendMessage, clearChat, addAnalysisMessage }
}
