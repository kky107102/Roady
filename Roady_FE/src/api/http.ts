import axios, { AxiosHeaders, type AxiosError, type InternalAxiosRequestConfig } from 'axios'

import type { ApiErrorResponse, TokenResponse } from '@/types/auth'
import { tokenStorage } from '@/utils/tokenStorage'

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

type SessionExpiredHandler = () => void

const baseURL = import.meta.env.VITE_API_BASE_URL

const http = axios.create({
  baseURL,
  timeout: 10_000,
  headers: {
    Accept: 'application/json',
  },
})

const refreshHttp = axios.create({
  baseURL,
  timeout: 10_000,
  headers: {
    Accept: 'application/json',
  },
})

let refreshPromise: Promise<string> | null = null
let sessionExpiredHandler: SessionExpiredHandler | null = null

export function setSessionExpiredHandler(handler: SessionExpiredHandler) {
  sessionExpiredHandler = handler
}

function isRefreshExcluded(url?: string) {
  return Boolean(url?.includes('/auth/login') || url?.includes('/auth/refresh'))
}

async function refreshAccessToken() {
  const refreshToken = tokenStorage.getRefreshToken()

  if (!refreshToken) {
    throw new Error('Refresh Token이 없습니다.')
  }

  const { data } = await refreshHttp.post<TokenResponse>('/auth/refresh', {
    refreshToken,
  })

  tokenStorage.save(data)
  return data.accessToken
}

http.interceptors.request.use((config) => {
  const accessToken = tokenStorage.getAccessToken()

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isRefreshExcluded(originalRequest.url)
    ) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })

      const accessToken = await refreshPromise
      originalRequest.headers = AxiosHeaders.from(originalRequest.headers)
      originalRequest.headers.set('Authorization', `Bearer ${accessToken}`)

      return http(originalRequest)
    } catch {
      tokenStorage.clear()
      sessionExpiredHandler?.()
      return Promise.reject(error)
    }
  },
)

export default http
