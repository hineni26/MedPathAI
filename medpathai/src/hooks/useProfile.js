import { useCallback, useEffect, useState } from 'react'
import { getProfile } from '../api/registration'
import { useUserStore } from '../store/userStore'
import { useUIStore } from '../store/uiStore'

export default function useProfile({ autoLoad = true } = {}) {
  const userId = useUserStore((s) => s.userId)
  const profile = useUserStore((s) => s.profile)
  const financials = useUserStore((s) => s.financials)
  const setProfile = useUserStore((s) => s.setProfile)
  const setFinancials = useUserStore((s) => s.setFinancials)
  const setDocuments = useUserStore((s) => s.setDocuments)
  const toast = useUIStore((s) => s.toast)
  const [loading, setLoading] = useState(autoLoad)

  const refreshProfile = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getProfile(userId)
      setProfile(data.profile || null)
      setFinancials(data.financials || null)
      setDocuments(data.documents || [])
      return data
    } catch (err) {
      toast(err.message || 'Could not load profile', 'error')
      throw err
    } finally {
      setLoading(false)
    }
  }, [setDocuments, setFinancials, setProfile, toast, userId])

  useEffect(() => {
    if (autoLoad && userId) {
      Promise.resolve().then(refreshProfile).catch(() => {})
    }
  }, [autoLoad, refreshProfile, userId])

  return {
    userId,
    profile,
    financials,
    loading,
    refreshProfile,
  }
}
