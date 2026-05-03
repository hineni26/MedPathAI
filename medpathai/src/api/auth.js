import client from './client'
import {
  ACCESS_TOKEN_KEY,
  REGISTERED_KEY,
  USER_ID_KEY,
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from './session'

// Generate a stable userId for this browser.
// In a real auth system this would come from a login token.
export function getUserId() {
  let userId = localStorage.getItem(USER_ID_KEY)
  if (!userId) {
    userId = 'user_' + Math.random().toString(36).slice(2, 11)
    localStorage.setItem(USER_ID_KEY, userId)
  }
  return userId
}

export function setUserId(userId) {
  localStorage.setItem(USER_ID_KEY, userId)
}

export function clearUserId() {
  localStorage.removeItem(USER_ID_KEY)
}

export function isRegistered() {
  return !!localStorage.getItem(REGISTERED_KEY) && !!localStorage.getItem(USER_ID_KEY) && !!getAccessToken()
}

export function markRegistered() {
  localStorage.setItem(REGISTERED_KEY, '1')
}

export function clearRegistration() {
  localStorage.removeItem(REGISTERED_KEY)
  clearAccessToken()
}

export const loginUser = (payload) =>
  client.post('/api/login', payload)

export { ACCESS_TOKEN_KEY, clearAccessToken, setAccessToken }
