export type UserRole = 'ADMIN' | 'INSPECTOR' | 'REPAIRER' | 'VIEWER'

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  tokenType: string
  accessToken: string
  refreshToken: string
  expiresInSeconds: number
}

export interface RefreshTokenRequest {
  refreshToken: string
}

export interface AuthUser {
  id: number
  username: string
  role: UserRole
}

export interface ApiErrorResponse {
  timestamp?: string
  status?: number
  message: string
  errors?: string[]
}
