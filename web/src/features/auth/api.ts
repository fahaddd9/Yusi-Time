import { apiClient } from "@/lib/api-client"

export const authApi = {
  signup: (data: { email: string; password: string; full_name: string; timezone?: string }) =>
    apiClient.post("/auth/signup", data),

  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),

  refresh: () => apiClient.post("/auth/refresh"),

  logout: () => apiClient.post("/auth/logout"),

  forgotPassword: (email: string) =>
    apiClient.post("/auth/forgot-password", { email }),

  resetPassword: (token: string, new_password: string) =>
    apiClient.post("/auth/reset-password", { token, new_password }),
}
