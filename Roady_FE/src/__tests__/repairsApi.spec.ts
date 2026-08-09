import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { RepairTransitionResult } from '@/types/repair'

const mocks = vi.hoisted(() => ({
  post: vi.fn<(url: string, payload?: unknown) => Promise<{ data: RepairTransitionResult }>>(),
  patch: vi.fn<(url: string, payload?: unknown) => Promise<{ data: RepairTransitionResult }>>(),
  clearDetailCache: vi.fn<(id?: number) => void>(),
}))

vi.mock('@/api/http', () => ({
  default: {
    post: mocks.post,
    patch: mocks.patch,
  },
}))

vi.mock('@/api/damages', () => ({
  damagesApi: {
    clearDetailCache: mocks.clearDetailCache,
  },
}))

import { repairsApi } from '@/api/repairs'

const updatedDamage = { id: 6 } as RepairTransitionResult

describe('repairsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('보수 요청 API를 호출하고 상세 캐시를 비운다', async () => {
    mocks.post.mockResolvedValue({ data: updatedDamage })

    await expect(repairsApi.submitRequest(6, { note: '요청 메모' })).resolves.toBe(updatedDamage)

    expect(mocks.post).toHaveBeenCalledWith('/damages/6/repair-request', {
      note: '요청 메모',
    })
    expect(mocks.clearDetailCache).toHaveBeenCalledWith(6)
  })

  it('보수 요청 취소 API를 PATCH로 호출한다', async () => {
    mocks.patch.mockResolvedValue({ data: updatedDamage })

    await expect(repairsApi.cancelRequest(6, { note: null })).resolves.toBe(updatedDamage)

    expect(mocks.patch).toHaveBeenCalledWith('/damages/6/repair-cancel', { note: null })
    expect(mocks.clearDetailCache).toHaveBeenCalledWith(6)
  })

  it('보수 요청서 수정 API를 PATCH로 호출한다', async () => {
    mocks.patch.mockResolvedValue({ data: updatedDamage })
    const payload = {
      note: '수정 메모',
      processingPriority: 'HIGH',
      reviewDamageType: 'WEAR',
      repairerId: 9,
    }

    await expect(repairsApi.updateRequest(6, payload)).resolves.toBe(updatedDamage)

    expect(mocks.patch).toHaveBeenCalledWith('/damages/6/repair-request', payload)
    expect(mocks.clearDetailCache).toHaveBeenCalledWith(6)
  })

  it('보수 완료 API를 PATCH로 호출한다', async () => {
    mocks.patch.mockResolvedValue({ data: updatedDamage })

    await expect(
      repairsApi.completeRepair(6, { completedAt: '2026-08-01', note: '완료 메모' }),
    ).resolves.toBe(updatedDamage)

    expect(mocks.patch).toHaveBeenCalledWith('/damages/6/repair-complete', {
      completedAt: '2026-08-01',
      note: '완료 메모',
    })
    expect(mocks.clearDetailCache).toHaveBeenCalledWith(6)
  })
})
