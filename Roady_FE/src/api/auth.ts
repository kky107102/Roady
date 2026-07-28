import http from './http'
import type { AuthUser, LoginRequest, RefreshTokenRequest, TokenResponse } from '@/types/auth'

export const authApi = {
  async login(payload: LoginRequest) {
    const { data } = await http.post<TokenResponse>('/auth/login', payload)
    return data
  },

  async refresh(payload: RefreshTokenRequest) {
    const { data } = await http.post<TokenResponse>('/auth/refresh', payload)
    return data
  },

  async logout(payload: RefreshTokenRequest) {
    await http.post('/auth/logout', payload)
  },

  async getMe() {
    const { data } = await http.get<AuthUser>('/auth/me')
    return data
  },
}
