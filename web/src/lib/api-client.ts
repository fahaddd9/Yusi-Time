import axios from 'axios'
import { tokenStore } from './token-store'

export const apiClient = axios.create({
  baseURL: 'http://localhost:8001/api/v1',
  withCredentials: true, // required for HttpOnly refresh cookie
})

// Attach access token from memory to every request
apiClient.interceptors.request.use((config) => {
  const token = tokenStore.getAccessToken()
  console.log(`[ApiClient] Request: ${config.method?.toUpperCase()} ${config.url} | HasToken: ${!!token}`)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Silent refresh on 401 → redirect to /login on failure
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[ApiClient] Response: ${response.config.method?.toUpperCase()} ${response.config.url} -> Status ${response.status}`)
    return response
  },
  async (error) => {
    console.error(`[ApiClient] Error Response: ${error.config?.method?.toUpperCase()} ${error.config?.url} -> Status ${error.response?.status}`)
    
    const isRefreshRequest = error.config?.url === '/auth/refresh'
    if (error.response?.status === 401 && !error.config?._retry && !isRefreshRequest) {
      console.log(`[ApiClient] Triggering silent refresh via interceptor for ${error.config.url}`)
      error.config._retry = true
      try {
        const { data } = await apiClient.post('/auth/refresh')
        console.log(`[ApiClient] Silent refresh succeeded. Retrying original request.`)
        tokenStore.setAccessToken(data.access_token)
        error.config.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(error.config)
      } catch (refreshError) {
        console.error(`[ApiClient] Silent refresh failed during interceptor loop:`, refreshError)
        tokenStore.clearAccessToken()
        if (typeof window !== 'undefined') {
          console.log(`[ApiClient] Forcing hard redirect to /login`)
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
