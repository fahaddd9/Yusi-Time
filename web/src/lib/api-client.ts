import axios from 'axios'
import { tokenStore } from './token-store'

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  withCredentials: true, // required for HttpOnly refresh cookie
})

// Attach access token from memory to every request
apiClient.interceptors.request.use((config) => {
  const token = tokenStore.getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Silent refresh on 401 → redirect to /login on failure
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      try {
        const { data } = await apiClient.post('/auth/refresh')
        tokenStore.setAccessToken(data.access_token)
        error.config.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(error.config)
      } catch {
        tokenStore.clearAccessToken()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
