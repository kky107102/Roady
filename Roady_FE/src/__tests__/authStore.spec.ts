import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'
import type { AuthUser, LoginRequest, RefreshTokenRequest, TokenResponse } from '@/types/auth'

const authApiMock = vi.hoisted(() => ({
  login: vi.fn<(payload: LoginRequest) => Promise<TokenResponse>>(),
  logout: vi.fn<(payload: RefreshTokenRequest) => Promise<void>>(),
  getMe: vi.fn<() => Promise<AuthUser>>(),
}))

vi.mock('@/api/auth', () => ({
  authApi: authApiMock,
}))

const tokens: TokenResponse = {
  tokenType: 'Bearer',
  accessToken: 'access-token',
  refreshToken: 'refresh-token',
  expiresInSeconds: 1800,
}

const user: AuthUser = {
  id: 1,
  username: 'admin',
  role: 'ADMIN',
}

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('로그인 성공 시 토큰과 사용자 정보를 저장한다', async () => {
    authApiMock.login.mockResolvedValue(tokens)
    authApiMock.getMe.mockResolvedValue(user)
    const store = useAuthStore()

    await store.login({ username: 'admin', password: 'admin1234' })

    expect(localStorage.getItem('accessToken')).toBe(tokens.accessToken)
    expect(localStorage.getItem('refreshToken')).toBe(tokens.refreshToken)
    expect(store.user).toEqual(user)
    expect(store.isAuthenticated).toBe(true)
  })

  it('저장된 토큰이 있으면 사용자 정보를 복원한다', async () => {
    localStorage.setItem('accessToken', tokens.accessToken)
    localStorage.setItem('refreshToken', tokens.refreshToken)
    authApiMock.getMe.mockResolvedValue(user)
    const store = useAuthStore()

    await store.restoreSession()

    expect(authApiMock.getMe).toHaveBeenCalledOnce()
    expect(store.user).toEqual(user)
    expect(store.initialized).toBe(true)
  })

  it('저장된 토큰이 없으면 사용자 조회를 요청하지 않는다', async () => {
    const store = useAuthStore()

    await store.restoreSession()

    expect(authApiMock.getMe).not.toHaveBeenCalled()
    expect(store.initialized).toBe(true)
    expect(store.isAuthenticated).toBe(false)
  })

  it('로그아웃 API가 실패해도 로컬 인증 정보를 제거한다', async () => {
    localStorage.setItem('accessToken', tokens.accessToken)
    localStorage.setItem('refreshToken', tokens.refreshToken)
    authApiMock.logout.mockRejectedValue(new Error('network error'))
    const store = useAuthStore()

    await expect(store.logout()).resolves.toBeUndefined()

    expect(localStorage.getItem('accessToken')).toBeNull()
    expect(localStorage.getItem('refreshToken')).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })
})
