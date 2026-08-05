<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import CommonMap from '@/components/common/CommonMap.vue'
import DashboardToolbar from '@/components/dashboard/DashboardToolbar.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import TrendChart from '@/components/dashboard/TrendChart.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import RecentDamageList from '@/components/damages/RecentDamageList.vue'
import UrgentDamageList from '@/components/damages/UrgentDamageList.vue'
import { toDamageMapMarkers } from '@/utils/damageMap'
import { reviewTabForDamage } from '@/utils/damageReview'

const store = useDashboardStore()
const router = useRouter()

const hasTrendData = computed(() => store.timeSeries.items.some((item) => item.totalCount > 0))

function damageDetailQuery(id: string | number) {
  const damage = store.damages.find((item) => String(item.id) === String(id))
  return {
    review: damage ? reviewTabForDamage(damage) : 'pending',
    damageId: String(id),
  }
}

const damageMarkers = computed(() =>
  toDamageMapMarkers(store.damages).map((marker) => ({
    ...marker,
    actionLabel: '상세보기',
    actionHref: router.resolve({
      name: 'damages',
      query: damageDetailQuery(marker.id),
    }).href,
  })),
)

function openDamageDetail(id: string | number) {
  router.push({ name: 'damages', query: damageDetailQuery(id) })
}

const REFRESH_MS = 5 * 60 * 1000

let refreshTimer: ReturnType<typeof setInterval> | null = null

function handleVisibilityChange() {
  if (!document.hidden) store.fetchAll()
}

onMounted(() => {
  store.fetchAll()
  refreshTimer = setInterval(() => {
    if (!document.hidden) store.fetchAll()
  }, REFRESH_MS)
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (refreshTimer !== null) clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<template>
  <div class="dashboard-view">
    <!-- 조회 조건 툴바 (전체 너비) -->
    <DashboardToolbar v-model="store.filter" @apply="store.applyFilter" />

    <!-- 스크롤 콘텐츠 영역 -->
    <div class="dashboard-scroll">
      <div class="dashboard">
        <!-- 로딩 오버레이 -->
        <div v-if="store.loading" class="dashboard__loading">
          <LoadingSpinner label="대시보드 데이터 불러오는 중" />
        </div>

        <!-- 인라인 에러 배너 (레이아웃은 유지) -->
        <div v-if="store.error && !store.loading" class="dashboard__error-banner" role="alert">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{{ store.error }}</span>
          <button type="button" class="error-banner__retry" @click="store.fetchAll">
            다시 시도
          </button>
        </div>

        <!-- 통계 요약 카드 -->
        <section class="dashboard__stats" aria-label="통계 요약">
          <StatCard
            label="신규 탐지"
            :count="store.newDetectionCount"
            :to="{ name: 'damages', query: { review: 'pending' } }"
          >
            <template #icon>
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </template>
          </StatCard>

          <StatCard
            label="긴급 확인 필요"
            :count="store.urgentReviewCount"
            variant="danger"
            :to="{ name: 'damages', query: { review: 'pending', sort: 'priority' } }"
          >
            <template #icon>
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path
                  d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </template>
          </StatCard>

          <StatCard
            label="요청 전"
            :count="store.requestedCount"
            :to="{ name: 'repairs', query: { statuses: 'REQUESTED' } }"
          >
            <template #icon>
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="8" y1="13" x2="16" y2="13" />
                <line x1="8" y1="17" x2="14" y2="17" />
              </svg>
            </template>
          </StatCard>

          <StatCard
            label="운행 중 로디"
            :count="store.activeRobotCount"
            variant="dark"
            :to="{ name: 'robots' }"
          >
            <template #icon>
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
              </svg>
            </template>
          </StatCard>
        </section>

        <!-- 메인 콘텐츠 영역 -->
        <div class="dashboard__main">
          <section class="dashboard__map-section" aria-label="실시간 탐지 현황">
            <div class="section-header">
              <div>
                <h2 class="section-title">실시간 탐지 현황</h2>
                <p class="section-subtitle">
                  현재 조회 기간에 수집된 탐지 사건 위치입니다. 마커를 선택하면 상태를 확인할 수
                  있습니다.
                </p>
              </div>
              <span class="map-marker-count">위치 확인 {{ damageMarkers.length }}건</span>
            </div>
            <CommonMap
              class="dashboard-map"
              :markers="damageMarkers"
              center-popup-on-select
              map-label="대시보드 실시간 탐지 현황 지도"
              empty-message="위치 정보가 있는 탐지 사건이 없습니다."
              @marker-select="openDamageDetail"
            />
          </section>

          <!-- 신규 탐지 알림 -->
          <section class="dashboard__alert-section" aria-label="신규 탐지 알림">
            <div class="section-header">
              <h2 class="section-title">신규 탐지 알림</h2>
            </div>
            <RecentDamageList />
          </section>
        </div>

        <!-- 하단 콘텐츠 영역 -->
        <div class="dashboard__bottom">
          <!-- 탐지 추이 차트 -->
          <section class="dashboard__chart-section" aria-label="탐지 추이 분석">
            <div class="section-header">
              <div>
                <h2 class="section-title">탐지 추이 분석</h2>
                <p class="section-subtitle">선택한 기간의 탐지 및 보수 완료 건수</p>
              </div>
            </div>
            <DashboardToolbar v-model="store.trendFilter" compact @apply="store.applyTrendFilter" />
            <div v-if="store.trendError" class="chart-error" role="alert">
              <span>{{ store.trendError }}</span>
              <button type="button" class="error-banner__retry" @click="store.fetchTrend">
                다시 시도
              </button>
            </div>
            <div v-if="!store.trendError" class="trend-chart-wrap" :aria-busy="store.trendLoading">
              <LoadingSpinner v-if="store.trendLoading" label="탐지 추이 데이터를 불러오는 중" />
              <div v-else-if="!hasTrendData" class="trend-empty" role="status">
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <path d="M3 3v18h18" />
                  <path d="m7 16 4-4 3 3 5-6" />
                </svg>
                <p>선택한 기간에 탐지된 사건이 없습니다.</p>
              </div>
              <TrendChart v-else :data="store.timeSeries" />
            </div>
          </section>

          <!-- 긴급 확인 필요 사건 -->
          <section class="dashboard__urgent-section" aria-label="긴급 확인 필요 사건">
            <div class="section-header">
              <h2 class="section-title">긴급 확인 필요 사건</h2>
            </div>
            <UrgentDamageList :items="store.urgentDamages" />
          </section>
        </div>
      </div>
      <!-- .dashboard -->
    </div>
    <!-- .dashboard-scroll -->
  </div>
  <!-- .dashboard-view -->
</template>

<style scoped>
/* ── 뷰 셸 ── */
.dashboard-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.dashboard-scroll {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.dashboard {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 2.4rem 3.2rem;
  min-width: 0;
}

/* ── 로딩 오버레이 ── */
.dashboard__loading {
  position: absolute;
  inset: 0;
  z-index: 10;
  background: rgb(255 255 255 / 60%);
}

/* ── 에러 배너 ── */
.dashboard__error-banner {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.7rem 1.4rem;
  border-radius: 0.6rem;
  border: 1px solid var(--roady-status-danger);
  background: color-mix(in srgb, var(--roady-status-danger) 8%, transparent);
  color: var(--roady-status-danger);
  font-size: var(--krds-pc-font-size-body-small);
}

.dashboard__error-banner span {
  flex: 1;
  color: var(--roady-text-primary);
}

.error-banner__retry {
  flex-shrink: 0;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--roady-status-danger);
  border-radius: 0.4rem;
  color: var(--roady-status-danger);
  background: transparent;
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
  transition: background-color 0.15s;
}

.error-banner__retry:hover {
  background: color-mix(in srgb, var(--roady-status-danger) 10%, transparent);
}

/* ── 통계 카드 행 ── */
.dashboard__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.6rem;
}

/* ── 메인 영역 (지도 + 알림) ── */
.dashboard__main {
  display: grid;
  grid-template-columns: 1fr 38rem;
  gap: 1.6rem;
  min-height: 36rem;
}

/* ── 하단 영역 (차트 + 긴급) ── */
.dashboard__bottom {
  display: grid;
  grid-template-columns: 1fr 38rem;
  gap: 1.6rem;
}

/* ── 공통 섹션 카드 ── */
.dashboard__map-section,
.dashboard__alert-section,
.dashboard__chart-section,
.dashboard__urgent-section {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
  padding: 2rem 2.4rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
  min-width: 0;
}

.trend-chart-wrap {
  min-height: 24rem;
  display: grid;
  place-items: center;
}

.trend-chart-wrap :deep(.trend-chart) {
  width: 100%;
}

.trend-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  color: var(--roady-text-tertiary);
  text-align: center;
}

.trend-empty p {
  margin: 0;
  font-size: var(--krds-pc-font-size-body-small);
}

.chart-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 1.2rem;
  border: 1px solid var(--roady-status-danger);
  border-radius: 0.6rem;
  color: var(--roady-status-danger);
  background: color-mix(in srgb, var(--roady-status-danger) 8%, transparent);
  font-size: var(--krds-pc-font-size-body-small);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.2rem;
}

.section-title {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-heading-xsmall);
  font-weight: var(--krds-font-weight-bold);
}

.section-subtitle {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin: 0.4rem 0 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

.dashboard-map {
  flex: 1;
  min-height: 30rem;
}

.map-marker-count {
  flex-shrink: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
}

/* ── 임시 데이터 배지 ── */
.mock-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  border-radius: 0.4rem;
  background: color-mix(in srgb, var(--roady-status-warning) 15%, transparent);
  color: var(--roady-status-warning);
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-weight: var(--krds-font-weight-bold);
  letter-spacing: 0.02em;
}

/* ── 1440px 이하 대응 ── */
@media (max-width: 1440px) {
  .dashboard__stats {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1280px) {
  .dashboard__main,
  .dashboard__bottom {
    grid-template-columns: 1fr;
  }
}
</style>
