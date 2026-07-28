import type { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ApiErrorResponse, TokenResponse } from '@/types/auth'

type RequestInterceptor = (config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig
type ResponseInterceptor = (response: AxiosResponse) => AxiosResponse
type ResponseErrorInterceptor = (error: AxiosError<ApiErrorResponse>) => Promise<unknown>

const axiosHarness = vi.hoisted(() => {
  const mainClient = Object.assign(
    vi.fn<(config: InternalAxiosRequestConfig) => Promise<AxiosResponse>>(),
    {
      interceptors: {
        request: {
          use: vi.fn<(fulfilled: RequestInterceptor) => number>(),
        },
        response: {
          use: vi.fn<
            (fulfilled: ResponseInterceptor, rejected: ResponseErrorInterceptor) => number
          >(),
        },
      },
    },
  )

  const refreshClient = {
    post: vi.fn<
      (url: string, payload: { refreshToken: string }) => Promise<{ data: TokenResponse }>
    >(),
  }

  return {
    mainClient,
    refreshClient,
    responseRejected: null as ((error: AxiosError<ApiErrorResponse>) => Promise<unknown>) | null,
  }
})

vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal<typeof import('axios')>()

  axiosHarness.mainClient.interceptors.request.use.mockImplementation(() => 0)
  axiosHarness.mainClient.interceptors.response.use.mockImplementation((_fulfilled, rejected) => {
    axiosHarness.responseRejected = rejected
    return 0
  })

  return {
    ...actual,
    default: {
      ...actual.default,
      create: vi
        .fn<() => typeof axiosHarness.mainClient | typeof axiosHarness.refreshClient>()
        .mockReturnValueOnce(axiosHarness.mainClient)
        .mockReturnValueOnce(axiosHarness.refreshClient),
    },
  }
})

const { setSessionExpiredHandler } = await import('@/api/http')

const refreshedTokens: TokenResponse = {
  tokenType: 'Bearer',
  accessToken: 'new-access-token',
  refreshToken: 'new-refresh-token',
  expiresInSeconds: 1800,
}

function unauthorizedError(url = '/damages') {
  return {
    config: {
      headers: {},
      method: 'get',
      url,
    },
    response: {
      status: 401,
    },
  } as AxiosError<ApiErrorResponse>
}

describe('http authentication interceptor', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    axiosHarness.mainClient.mockResolvedValue({
      data: { retried: true },
    } as AxiosResponse)
  })

  it('401 응답이면 토큰을 재발급하고 기존 요청을 재시도한다', async () => {
    localStorage.setItem('refreshToken', 'old-refresh-token')
    axiosHarness.refreshClient.post.mockResolvedValue({ data: refreshedTokens })

    await axiosHarness.responseRejected?.(unauthorizedError())

    expect(axiosHarness.refreshClient.post).toHaveBeenCalledWith('/auth/refresh', {
      refreshToken: 'old-refresh-token',
    })
    expect(localStorage.getItem('accessToken')).toBe(refreshedTokens.accessToken)
    expect(localStorage.getItem('refreshToken')).toBe(refreshedTokens.refreshToken)
    expect(axiosHarness.mainClient).toHaveBeenCalledOnce()

    const retriedRequest = axiosHarness.mainClient.mock.calls[0]?.[0]
    expect(retriedRequest?.headers.get('Authorization')).toBe(
      `Bearer ${refreshedTokens.accessToken}`,
    )
  })

  it('재발급에 실패하면 토큰을 제거하고 세션 만료 처리를 실행한다', async () => {
    localStorage.setItem('accessToken', 'expired-access-token')
    localStorage.setItem('refreshToken', 'expired-refresh-token')
    axiosHarness.refreshClient.post.mockRejectedValue(new Error('refresh failed'))
    const handleSessionExpired = vi.fn<() => void>()
    setSessionExpiredHandler(handleSessionExpired)

    await expect(axiosHarness.responseRejected?.(unauthorizedError())).rejects.toMatchObject({
      response: { status: 401 },
    })

    expect(localStorage.getItem('accessToken')).toBeNull()
    expect(localStorage.getItem('refreshToken')).toBeNull()
    expect(handleSessionExpired).toHaveBeenCalledOnce()
    expect(axiosHarness.mainClient).not.toHaveBeenCalled()
  })
})
