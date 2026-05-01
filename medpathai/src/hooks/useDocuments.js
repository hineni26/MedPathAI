import { useCallback, useEffect, useState } from 'react'
import { getDocuments } from '../api/documents'
import { useUserStore } from '../store/userStore'
import { useUIStore } from '../store/uiStore'

export default function useDocuments({ autoLoad = true } = {}) {
  const userId = useUserStore((s) => s.userId)
  const documents = useUserStore((s) => s.documents)
  const setDocuments = useUserStore((s) => s.setDocuments)
  const toast = useUIStore((s) => s.toast)
  const [loading, setLoading] = useState(autoLoad)

  const refreshDocuments = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getDocuments(userId)
      const docs = data.documents || []
      setDocuments(docs)
      return docs
    } catch (err) {
      toast(err.message || 'Could not load documents', 'error')
      throw err
    } finally {
      setLoading(false)
    }
  }, [setDocuments, toast, userId])

  useEffect(() => {
    if (autoLoad && userId) {
      Promise.resolve().then(refreshDocuments).catch(() => {})
    }
  }, [autoLoad, refreshDocuments, userId])

  return { userId, documents, loading, refreshDocuments }
}
