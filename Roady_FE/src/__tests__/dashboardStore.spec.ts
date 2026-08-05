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
      page: 0,
      size: 100,
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

  it('미확인·긴급·요청 전 사건과 운행 중 로디를 각각 집계한다', async () => {
    damagesApiMock.list.mockResolvedValue({
      ...damageResponse,
      totalElements: 5,
      content: [
        {
          id: 1,
          currentStatus: 'AI_ANALYZED',
          repairPriority: 'URGENT',
          createdAt: '2026-08-05T01:00:00',
        },
        {
          id: 2,
          currentStatus: 'AI_ANALYZED',
          repairPriority: 'HIGH',
          createdAt: '2026-08-05T02:00:00',
        },
        {
          id: 3,
          currentStatus: 'REQUESTED',
          repairPriority: 'URGENT',
          createdAt: '2026-08-05T03:00:00',
        },
        {
          id: 4,
          currentStatus: 'REPAIR_IN_PROGRESS',
          repairPriority: 'NORMAL',
          createdAt: '2026-08-05T04:00:00',
        },
        {
          id: 5,
          currentStatus: 'CANCELED',
          repairPriority: 'URGENT',
          createdAt: '2026-08-05T05:00:00',
        },
      ],
    })
    robotsApiMock.list.mockResolvedValue([
      { id: 1, active: true, status: 'MOVING' },
      { id: 2, active: false, status: 'MOVING' },
      { id: 3, active: true, status: 'STANDBY' },
    ])
    const store = useDashboardStore()

    await store.fetchOverview()

    expect(store.newDetectionCount).toBe(2)
    expect(store.urgentReviewCount).toBe(1)
    expect(store.urgentDamages.map((item) => item.id)).toEqual([1])
    expect(store.requestedCount).toBe(1)
    expect(store.activeRobotCount).toBe(1)
  })
})
