import client from './client'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Upload uses multipart/form-data — bypass the JSON client
export async function uploadDocument(userId, docType, file, onProgress) {
  const formData = new FormData()
  formData.append('user_id', userId)
  formData.append('doc_type', docType)
  formData.append('file', file)

  const response = await axios.post(`${BASE_URL}/api/documents/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
  return response.data
}

export const getDocuments = (userId) =>
  client.get(`/api/documents/${userId}`)

export async function replaceDocument(userId, documentId, file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.put(`${BASE_URL}/api/documents/${userId}/${documentId}/file`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
  return response.data
}

export const deleteDocument = (userId, documentId) =>
  client.delete(`/api/documents/${userId}/${documentId}`)
