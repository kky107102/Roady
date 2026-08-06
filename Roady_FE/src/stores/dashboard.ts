import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { damagesApi } from '@/api/damages'
import { robotsApi } from '@/api/robots'
import { statisticsApi } from '@/api/statistics'
import type { DamageListItem } from '@/types/damage'
import type { Robot } from '@/types/robot'
import { isMovingAndConnected } from '@/utils/robotDisplay'
import type { StatUnit, TimeSeriesResponse } from '@/types/statistics'
import {
  localDateOffset,
  todayLocalStr,
  toApiFromDateTime,
  toApiToDateTime,
} from '@/utils/localDate'

const DASHBOARD_PAGE_SIZE = 100

export interface DashboardFilter {
  from: string
  to: string
  regionCode: string
}

function defaultFilter(): DashboardFilter {
  return { from: localDateOffset(6), to: todayLocalStr(), regionCode: '' }
}

function chartUnit(from: string, to: string): StatUnit {
  const dayMilliseconds = 24 * 60 * 60 * 1000
  const days = Math.ceil((new Date(to).getTime() - new Date(from).getTime()) / dayMilliseconds) + 1

  if (days > 730) return 'YEAR'
  if (days > 120) return 'MONTH'
  if (days > 31) return 'WEEK'
  return 'DAY'
}

export const useDashboardStore = defineStore('dashboard', () => {
  const filter = ref<DashboardFilter>(defaultFilter())
  const trendFilter = ref<DashboardFilter>(defaultFilter())
  const damages = ref<DamageListItem[]>([])
  const damagesTotalElements = ref(0)
  const robots = ref<Robot[]>([])
  const timeSeries = ref<TimeSeriesResponse>({ unit: 'DAY', items: [] })

  const loading = ref(false)
  const error = ref<string | null>(null)
  const trendLoading = ref(false)
  const trendError = ref<string | null>(null)

  const totalCount = computed(() => damagesTotalElements.value)
  const newDetectionCount = computed(
    () => damages.value.filter((damage) => damage.currentStatus === 'AI_ANALYZED').length,
  )
  const reviewRequiredCount = computed(() => newDetectionCount.value)
  const urgentDamages = computed(() =>
    damages.value
      .filter(
        (damage) => damage.currentStatus === 'AI_ANALYZED' && damage.repairPriority === 'URGENT',
      )
      .sort((left, right) => {
        const leftTime = Date.parse(left.capturedAt ?? left.createdAt)
        const rightTime = Date.parse(right.capturedAt ?? right.createdAt)
        return rightTime - leftTime || right.id - left.id
      }),
  )
  const urgentReviewCount = computed(() => urgentDamages.value.length)
  const requestedCount = computed(
    () => damages.value.filter((damage) => damage.currentStatus === 'REQUESTED').length,
  )
  const repairingCount = computed(
    () => damages.value.filter((damage) => damage.currentStatus === 'REPAIR_IN_PROGRESS').length,
  )
  const highSeverityCount = computed(() => urgentReviewCount.value)
  const activeRobotCount = computed(
    () => robots.value.filter(isMovingAndConnected).length,
  )

  async function refreshRobots() {
    robots.value = await robotsApi.list()
  }

  async function fetchOverview() {
    loading.value = true
    error.value = null

    try {
      const queryParams = {
        ...(filter.value.from ? { from: toApiFromDateTime(filter.value.from) } : {}),
        ...(filter.value.to ? { to: toApiToDateTime(filter.value.to) } : {}),
      }
      const firstDamagePagePromise = damagesApi.list({
        ...queryParams,
        page: 0,
        size: DASHBOARD_PAGE_SIZE,
      })
      const [firstDamagePage, robotList] = await Promise.all([
        firstDamagePagePromise,
        robotsApi.list(),
      ])
      const remainingPages = await Promise.all(
        Array.from({ length: Math.max(0, firstDamagePage.totalPages - 1) }, (_, index) =>
          damagesApi.list({
            ...queryParams,
            page: index + 1,
            size: DASHBOARD_PAGE_SIZE,
          }),
        ),
      )
      damages.value = [firstDamagePage, ...remainingPages].flatMap((page) => page.content)
      damagesTotalElements.value = firstDamagePage.totalElements
      robots.value = robotList
    } catch (fetchError: unknown) {
      if (import.meta.env.DEV) console.error('[Dashboard] fetchOverview:', fetchError)
      error.value = '데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
    } finally {
      loading.value = false
    }
  }

  async function fetchTrend() {
    trendLoading.value = true
    trendError.value = null

    try {
      const from = trendFilter.value.from || localDateOffset(6)
      const to = trendFilter.value.to || todayLocalStr()
      timeSeries.value = await statisticsApi.timeSeries({
        from: toApiFromDateTime(from),
        to: toApiToDateTime(to),
        unit: chartUnit(from, to),
      })
    } catch (fetchError: unknown) {
      if (import.meta.env.DEV) console.error('[Dashboard] fetchTrend:', fetchError)
      trendError.value = '탐지 추이 데이터를 불러오지 못했습니다.'
    } finally {
      trendLoading.value = false
    }
  }

  async function fetchAll() {
    await Promise.all([fetchOverview(), fetchTrend()])
  }

  async function applyFilter(newFilter: DashboardFilter) {
    filter.value = { ...newFilter }
    await fetchOverview()
  }

  async function applyTrendFilter(newFilter: DashboardFilter) {
    trendFilter.value = { ...newFilter }
    await fetchTrend()
  }

  return {
    filter,
    trendFilter,
    damages,
    damagesTotalElements,
    robots,
    timeSeries,
    loading,
    error,
    trendLoading,
    trendError,
    totalCount,
    newDetectionCount,
    reviewRequiredCount,
    urgentDamages,
    urgentReviewCount,
    requestedCount,
    repairingCount,
    highSeverityCount,
    activeRobotCount,
    fetchAll,
    fetchOverview,
    fetchTrend,
    refreshRobots,
    applyFilter,
    applyTrendFilter,
  }
})
