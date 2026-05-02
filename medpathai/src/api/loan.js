import client from './client'

export const applyLoan = (payload) =>
  client.post('/api/loan/apply', payload)
// payload: { user_id, session_id, loan_amount, tenure_months }

export const getLoanApplications = (userId) =>
  client.get(`/api/loan/applications/${userId}`)
