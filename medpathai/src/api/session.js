export const USER_ID_KEY = 'medpath_user_id'
export const REGISTERED_KEY = 'medpath_registered'
export const ACCESS_TOKEN_KEY = 'medpath_access_token'
export const OFFICER_TOKEN_KEY = 'medpath_officer_access_token'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token) {
  if (token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
  }
}

export function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

export function getOfficerToken() {
  return localStorage.getItem(OFFICER_TOKEN_KEY)
}

export function setOfficerToken(token) {
  if (token) {
    localStorage.setItem(OFFICER_TOKEN_KEY, token)
  }
}

export function clearOfficerToken() {
  localStorage.removeItem(OFFICER_TOKEN_KEY)
}
