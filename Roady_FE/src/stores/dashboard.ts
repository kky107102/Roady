import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import { damagesApi } from '@/api/damages'
import { robotsApi } from '@/api/robots'
import { MOCK_TIME_SERIES, MOCK_HIGH_SEVERITY_COUNT, MOCK_STAT_COUNTS } from '@/mocks/dashboard'
import type { DamageListItem } from '@/types/damage'
import type { Robot } from '@/types/robot'
import type { TimeSeriesResponse } from '@/types/statistics'

export interface DashboardFilter {
  from: string
  to: string
  regionCode: string
}

function toDateString(date: Date) {
  return date.toISOString().slice(0, 10)
}

function defaultFilter(): DashboardFilter {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - 6)
  return { from: toDateString(from), to: toDateString(to), regionCode: '' }
}

export const useDashboardStore = defineStore('dashboard', () => {
  const filter = ref<DashboardFilter>(defaultFilter())

  const damages = ref<DamageListItem[]>([])
  const damagesTotalElements = ref(0)
  const robots = ref<Robot[]>([])
  const timeSeries = ref<TimeSeriesResponse>(MOCK_TIME_SERIES)

  const loading = ref(false)
  const error = ref<string | null>(null)

  // ── 통계 요약 카드 ──────────────────────────────────────────
  // dev 환경에서 API 오류 시 mock 값을 폴백으로 사용한다.
  const useMock = computed(() => import.meta.env.DEV && !!error.value && !loading.value)

  const totalCount = computed(() =>
    useMock.value ? MOCK_STAT_COUNTS.total : damagesTotalElements.value,
  )

  const reviewRequiredCount = computed(() =>
    useMock.value
      ? MOCK_STAT_COUNTS.reviewRequired
      : damages.value.filter((d) => d.currentStatus === 'REVIEW_REQUIRED').length,
  )

  const repairingCount = computed(() =>
    useMock.value
      ? MOCK_STAT_COUNTS.repairing
      : damages.value.filter((d) => d.currentStatus === 'REPAIRING').length,
  )

  // severity 필드는 현재 API 응답에 포함되지 않으므로 항상 mock 값 사용
  const highSeverityCount = computed(() =>
    useMock.value ? MOCK_STAT_COUNTS.highSeverity : MOCK_HIGH_SEVERITY_COUNT,
  )

  const activeRobotCount = computed(() =>
    useMock.value
      ? MOCK_STAT_COUNTS.activeRobots
      : robots.value.filter((r) => r.active && r.status === 'MOVING').length,
  )

  // ── 데이터 조회 ─────────────────────────────────────────────
  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const queryParams = {
        from: filter.value.from,
        to: filter.value.to,
      }
      const [damageResponse, robotList] = await Promise.all([
        damagesApi.list(queryParams),
        robotsApi.list(),
      ])
      damages.value = damageResponse.content
      damagesTotalElements.value = damageResponse.totalElements
      robots.value = robotList
      // 통계 API 구현 후 아래 주석을 풀어 교체한다.
      // timeSeries.value = await statisticsApi.timeSeries({ ...queryParams, unit: 'DAY' })
    } catch (e: unknown) {
      if (import.meta.env.DEV) console.error('[Dashboard] fetchAll:', e)
      error.value = '데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
    } finally {
      loading.value = false
    }
  }

  function applyFilter(newFilter: DashboardFilter) {
    filter.value = { ...newFilter }
    fetchAll()
  }

  return {
    filter,
    damages,
    damagesTotalElements,
    robots,
    timeSeries,
    loading,
    error,
    totalCount,
    reviewRequiredCount,
    repairingCount,
    highSeverityCount,
    activeRobotCount,
    fetchAll,
    applyFilter,
  }
})
