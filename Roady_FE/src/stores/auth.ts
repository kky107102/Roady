import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi } from '@/api/auth'
import type { AuthUser, LoginRequest, TokenResponse } from '@/types/auth'
import { tokenStorage } from '@/utils/tokenStorage'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(tokenStorage.getAccessToken())
  const refreshToken = ref(tokenStorage.getRefreshToken())
  const user = ref<AuthUser | null>(null)
  const initialized = ref(false)

  const isAuthenticated = computed(() => Boolean(accessToken.value))

  function saveTokens(tokens: TokenResponse) {
    accessToken.value = tokens.accessToken
    refreshToken.value = tokens.refreshToken
    tokenStorage.save(tokens)
  }

  function clearSession() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    tokenStorage.clear()
  }

  async function login(payload: LoginRequest) {
    const tokens = await authApi.login(payload)
    saveTokens(tokens)

    try {
      user.value = await authApi.getMe()
    } catch (error) {
      clearSession()
      throw error
    }
  }

  async function restoreSession() {
    if (initialized.value) {
      return
    }

    if (!tokenStorage.hasSession()) {
      initialized.value = true
      return
    }

    try {
      user.value = await authApi.getMe()
      accessToken.value = tokenStorage.getAccessToken()
      refreshToken.value = tokenStorage.getRefreshToken()
    } catch {
      clearSession()
    } finally {
      initialized.value = true
    }
  }

  async function logout() {
    const token = tokenStorage.getRefreshToken()

    try {
      if (token) {
        await authApi.logout({ refreshToken: token })
      }
    } catch {
      // 서버 로그아웃 실패 여부와 관계없이 로컬 세션은 종료한다.
    } finally {
      clearSession()
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    initialized,
    isAuthenticated,
    login,
    logout,
    restoreSession,
    clearSession,
    saveTokens,
  }
})
