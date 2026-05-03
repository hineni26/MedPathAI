import axios from 'axios'
import { getAccessToken, getOfficerToken } from './session'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const PFL_API_KEY = import.meta.env.VITE_PFL_OFFICER_API_KEY

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60s — LangGraph pipeline can be slow
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const url = config.url || ''
  if (url.startsWith('/api/pfl')) {
    const officerToken = getOfficerToken()
    if (officerToken) {
      config.headers.Authorization = `Bearer ${officerToken}`
    } else if (PFL_API_KEY) {
      config.headers['X-PFL-API-Key'] = PFL_API_KEY
    }
    return config
  }

  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

// ── Response interceptor — normalise errors ──────────────────
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Something went wrong'
    return Promise.reject(new Error(message))
  }
)

export default client
