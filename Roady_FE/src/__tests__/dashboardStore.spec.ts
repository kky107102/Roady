import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const damagesApiMock = vi.hoisted(() => ({ list: vi.fn() }))
const robotsApiMock = vi.hoisted(() => ({ list: vi.fn() }))
const statisticsApiMock = vi.hoisted(() => ({ timeSeries: vi.fn() }))

vi.mock('@/api/damages', () => ({ damagesApi: damagesApiMock }))
vi.mock('@/api/robots', () => ({ robotsApi: robotsApiMock }))
vi.mock('@/api/statistics', () => ({ statisticsApi: statisticsApiMock }))

const damageResponse = {
  content: [],
  page: 0,
  size: 20,
  totalElements: 12,
  totalPages: 1,
}
const timeSeries = {
  unit: 'DAY' as const,
  items: [
    {
      period: '2026-08-01',
      totalCount: 5,
      repairCompletedCount: 2,
      repairCompletionRate: 40,
    },
  ],
}

describe('dashboard store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    damagesApiMock.list.mockResolvedValue(damageResponse)
    robotsApiMock.list.mockResolvedValue([])
    statisticsApiMock.timeSeries.mockResolvedValue(timeSeries)
  })

  it('전체 조회 기간과 탐지 추이 기간을 각각 적용한다', async () => {
    const store = useDashboardStore()
    store.filter = { from: '2026-08-01', to: '2026-08-07', regionCode: '' }
    store.trendFilter = { from: '2026-07-01', to: '2026-07-31', regionCode: '' }

    await store.fetchAll()

    expect(damagesApiMock.list).toHaveBeenCalledWith({
      from: '2026-08-01T00:00:00',
      to: '2026-08-08T00:00:00',
    })
    expect(statisticsApiMock.timeSeries).toHaveBeenCalledWith({
      from: '2026-07-01T00:00:00',
      to: '2026-08-01T00:00:00',
      unit: 'DAY',
    })
    expect(store.timeSeries).toEqual(timeSeries)
  })

  it('탐지 추이 기간 변경은 차트만 다시 조회한다', async () => {
    const store = useDashboardStore()

    await store.applyTrendFilter({
      from: '2026-06-01',
      to: '2026-08-01',
      regionCode: '',
    })

    expect(statisticsApiMock.timeSeries).toHaveBeenCalledWith(
      expect.objectContaining({ unit: 'WEEK' }),
    )
    expect(damagesApiMock.list).not.toHaveBeenCalled()
    expect(robotsApiMock.list).not.toHaveBeenCalled()
  })

  it('상단 기간 변경은 차트를 다시 조회하지 않는다', async () => {
    const store = useDashboardStore()

    await store.applyFilter({ from: '2026-08-01', to: '2026-08-05', regionCode: '' })

    expect(damagesApiMock.list).toHaveBeenCalledOnce()
    expect(statisticsApiMock.timeSeries).not.toHaveBeenCalled()
  })
})
