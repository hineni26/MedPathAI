import { useState } from 'react'
import { applyLoan } from '../api/loan'
import { useChatStore } from '../store/chatStore'
import { useUserStore } from '../store/userStore'
import { useUIStore } from '../store/uiStore'

export default function useLoan() {
  const userId = useUserStore((s) => s.userId)
  const sessionId = useChatStore((s) => s.sessionId)
  const toast = useUIStore((s) => s.toast)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  async function submitLoan({ loanAmount, tenureMonths = 24 }) {
    if (!sessionId) {
      toast('Start a chat before applying for a loan', 'warning')
      return null
    }

    setLoading(true)
    try {
      const data = await applyLoan({
        user_id: userId,
        session_id: sessionId,
        loan_amount: Number(loanAmount),
        tenure_months: Number(tenureMonths),
      })
      setResult(data)
      toast(data.message || 'Loan request submitted', data.success ? 'success' : 'warning')
      return data
    } catch (err) {
      toast(err.message || 'Could not submit loan request', 'error')
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { loading, result, submitLoan }
}
