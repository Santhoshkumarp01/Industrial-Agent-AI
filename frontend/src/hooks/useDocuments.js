import { useState, useCallback, useEffect } from 'react'
import {
  getDocuments as apiFetchDocs,
  uploadDocument as apiUpload,
  deleteDocument as apiDelete,
} from '../services/api'

export const useDocuments = () => {
  const [documents, setDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const docs = await apiFetchDocs()
      setDocuments(docs)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const uploadDocument = useCallback(
    async (file, equipmentTag, onProgress) => {
      setError(null)
      try {
        const result = await apiUpload(file, equipmentTag, onProgress)
        await fetchDocuments()
        return result
      } catch (err) {
        setError(err.message)
        throw err
      }
    },
    [fetchDocuments]
  )

  const deleteDocument = useCallback(
    async (docId) => {
      setError(null)
      try {
        await apiDelete(docId)
        setDocuments((prev) => prev.filter((d) => d.doc_id !== docId))
      } catch (err) {
        setError(err.message)
        throw err
      }
    },
    []
  )

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  return { documents, isLoading, error, fetchDocuments, uploadDocument, deleteDocument }
}
