import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { UserSummary } from '@/types/auth'

const mocks = vi.hoisted(() => ({
  get: vi.fn<(url: string, config?: unknown) => Promise<{ data: UserSummary[] }>>(),
}))

vi.mock('@/api/http', () => ({
  default: { get: mocks.get },
}))

import { usersApi } from '@/api/users'

describe('usersApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('활성 보수 담당자만 조회하도록 필터를 전달한다', async () => {
    mocks.get.mockResolvedValue({ data: [] })

    await usersApi.list({ role: 'REPAIRER', active: true })

    expect(mocks.get).toHaveBeenCalledWith('/users', {
      params: { role: 'REPAIRER', active: true },
    })
  })
})
